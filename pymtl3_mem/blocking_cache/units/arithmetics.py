"""
=========================================================================
arithmetic.py
=========================================================================
Combined arithmetic modules for the cache such as modified adders,
multipliers and comparators. Also include replicators

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

from pymtl3                  import *
from pymtl3.stdlib.primitive import RegEnRst, RegEn, Mux
from pymtl3_mem.constants    import *
from ..cache_constants       import *

class DataReplicator( Component ):
  """
  Makes incoming data bitwidth match the cacheline bitwdith

  AMO: zero extend the data to cacheline bitwidth
  Non-AMO: replicated data extend cacheline_bitwidth/data_bitwidth times
  """
  def construct( s , p ):

    s.in_  = InPort (p.bitwidth_data)
    s.len_ = InPort (p.bitwidth_len)
    s.amo  = InPort ()
    s.out  = OutPort(p.bitwidth_cacheline)

    # Each base 2 byte access needs one replicator
    nreplicators = clog2(p.bitwidth_data) - 2
    s.replications = [ Wire(p.bitwidth_cacheline) for i in range(nreplicators) ]
    # Replication extending
    for i in range(nreplicators):
      subwd_bitwidth = 2**(3 + i)
      for j in range(0, p.bitwidth_cacheline, subwd_bitwidth):
        s.replications[i][ j : j + subwd_bitwidth] //= s.in_[0 : subwd_bitwidth]

    # moyang: this is hack to let len==3 means zero-extending input data
    # to double-word (64-bit)
    s.double_word = Wire( p.bitwidth_cacheline )
    if p.bitwidth_data == 32 and p.bitwidth_cacheline >= 64:
      for j in range(0, p.bitwidth_cacheline, 64):
        s.double_word[j:j+64] //= lambda: zext( s.in_, 64 )
    else:
      s.double_word //= 0

    # Number of inputs to the output mux
    ninputs = nreplicators + 2 # 1 extra for AMO inputs, 1 extra for double-word (see below)
    s.output_mux = Mux(p.bitwidth_cacheline, ninputs)

    s.output_mux.in_[ninputs-1] //= s.double_word

    # Input 0 is reserved for AMO
    s.output_mux.in_[0][0 : p.bitwidth_data] //= s.in_[0 : p.bitwidth_data]
    # Address condition when cachline bitwidth is greater than data bitwidth where
    # we zero extend to match cacheline bitwidth
    if p.bitwidth_cacheline > p.bitwidth_data:
      s.output_mux.in_[0][p.bitwidth_data : p.bitwidth_cacheline] //= 0

    # Connect the outputs of all the replicator to the inputs of the output mux
    for i in range(ninputs - 2):
      s.output_mux.in_[i+1] //= s.replications[i]

    BitsSel = mk_bits( clog2(ninputs) )
    BitsLen = mk_bits( p.bitwidth_len )

    @update
    def output_mux_selection_logic():
      s.output_mux.sel @= 0
      if ~s.amo:
        s.output_mux.sel @= BitsSel(ninputs-2)
        if s.len_ == BitsLen(0):
          # choose the largest byte access available if len is 0
          s.output_mux.sel @= BitsSel(ninputs-2)
        elif s.len_ == BitsLen(3):
          s.output_mux.sel @= BitsSel(ninputs-1)
        else:
          # Iterate to check for matching len and then map to appropriate select
          for i in range(ninputs - 3):
            if s.len_ == BitsLen(2**i):
              s.output_mux.sel @= BitsSel(i) + 1
    s.out //= s.output_mux.out

  def line_trace( s ):
    msg = f'i[{s.in_}] o[{s.out}] amo:{s.amo} sel[{s.output_mux.sel}] len[{s.len_}]'
    return msg

class Indexer( Component ):
  """
  Calculates the index for the data array. This is mainly used for multi-way associative
  caches where we use one large data array instead of multiple tag arrays to store the
  data.

  For dmapped cache, this unit won't do anything and will be optimized away.
  """
  def construct ( s, p ):

    s.index  = InPort(p.bitwidth_index)
    s.offset = InPort(p.bitwidth_clog_asso)
    s.out    = OutPort(p.bitwidth_num_lines)

    BitsClogNlines  = mk_bits(p.bitwidth_num_lines)
    @update
    def index_logic():
      # zero extend the index to the index bitwidth and then apply offset depending
      # on which way we want to access. For Dmapped, the offset will always be 0.
      s.out @= zext(s.index, p.bitwidth_num_lines) + zext(s.offset, p.bitwidth_num_lines) * \
               trunc( Bits32(p.nblocks_per_way), p.bitwidth_num_lines )
      # Had to make it 32 bits so that we can truncate. May need to be fixed

  def line_trace( s ):
    msg = ""
    msg = f"idx:{s.index} off:{s.offset} "
    return msg

class OffsetLenSelector( Component ):
  """
  Selects the memory request len and address offset based on whether or not
  the transaction is an AMO

  If the transaction is an AMO, it will set offset to offset from the
  transaction and set the len to 4 since we only support word AMO

  If not AMO, then we set len to 0 for full line access and offset to 0
  """
  def construct(s, p):
    s.len_i    = InPort(p.bitwidth_len)
    s.offset_i = InPort(p.bitwidth_offset)
    s.is_amo   = InPort()
    s.offset_o = OutPort(p.bitwidth_offset)
    s.len_o    = OutPort(p.bitwidth_mem_len)

    s.amo_len = Wire(p.bitwidth_mem_len)

    # Special condition for when the data bitwidth is 32 bits where
    # the len field for the cache is 0 but the memrequest must be 4
    # for word access.
    if p.bitwidth_data == 32:
      s.amo_len //= 4
    else:
      s.amo_len //= lambda: zext(s.len_i, p.bitwidth_mem_len)

    @update
    def offset_selection_logic():
      if s.is_amo:
        s.offset_o @= s.offset_i
        s.len_o    @= s.amo_len # one word read always for len
      else:
        # Not AMO, the we want full line access where offset doesn't matter
        s.offset_o @= 0
        s.len_o    @= 0

class WriteBitEnGen( Component ):
  """
  Decodes the write bit enable for data array based on whether the cache is
  processing a regular request or a refill

  Assumes that the SRAM has bit enables
  """
  def construct(s, p):
    s.cmd      = InPort(2) # commmand based on what to generate
    s.dty_mask = InPort(p.bitwidth_dirty)
    s.offset   = InPort(p.bitwidth_offset)
    s.len_     = InPort(p.bitwidth_len)
    s.out      = OutPort(p.bitwidth_data_wben)

    bitwidth_nbyte = p.bitwidth_data_wben // 8
    s.word_mask = Wire( bitwidth_nbyte )
    nlens = clog2( p.bitwidth_data ) - 2

    # NOTE this is hardcoded to work for up to 128 bit data access
    assert( p.bitwidth_data >= 32 )

    @update
    def req_word_mask_logic():
      # Take advantage of bitwidth truncation to select word mask depending on
      # the data bitwidth
      if s.len_ == 1:
        s.word_mask @= 0b1
      elif s.len_ == 2: # assuming that data bitwidth >= 32
        s.word_mask @= 0b11
      elif s.len_ == 3:
        # moyang: this is a hack for CIFER project. When len == 3, we zero-extend the 32-bit word to 64-bit
        s.word_mask @= 0b11111111
      elif s.len_ == trunc(Bits32(4), p.bitwidth_len):
        # truncated to 0 if 32 bit data
        s.word_mask @= 0b1111
      elif s.len_ == trunc(Bits32(8), p.bitwidth_len):
        # truncated to 0 if 64 bit data
        s.word_mask @= 0b11111111
      elif s.len_ == trunc(Bits32(16), p.bitwidth_len):
        # truncated to 0 if 128 bit data
        s.word_mask @= 0xffff
      else:
        s.word_mask @= 0

    s.shifted = Wire( bitwidth_nbyte )
    s.shifted //= lambda: s.word_mask << zext(s.offset, bitwidth_nbyte)

    s.wben_req   = Wire(p.bitwidth_data_wben)
    s.wben_dirty = Wire(p.bitwidth_data_wben)
    bitwidth_clog_nbyte = clog2(bitwidth_nbyte)
    bitwidth_clog_dirty = clog2(p.bitwidth_dirty)

    @update
    def wben_shift_logic():
      # Map byte access to bits access mask:
      # ex: 0x1 -> 0xff
      for i in range( p.bitwidth_data_wben ):
        i_byte = trunc(Bits32(i >> 3), bitwidth_clog_nbyte)
        i_mask = trunc(Bits32(i >> 5), bitwidth_clog_dirty)
        s.wben_req[i]   @= s.shifted[ i_byte ]
        s.wben_dirty[i] @= ~(s.dty_mask[ i_mask ])

    @update
    def output_logic():
      if s.cmd == WriteBitEnGen_CMD_REQ:
        # if this is a write request, then the wben depends on offset
        s.out @= s.wben_req
      elif s.cmd == WriteBitEnGen_CMD_DIRTY:
        # we are refilling, then the wben depends on the dirty bits
        s.out @= s.wben_dirty
      else: # s.cmd == WriteBitEnGen_CMD_NONE
        s.out @= 0

  def line_trace( s ):
    msg = f'o[{s.out}] '
    return msg

class TagArrayRDataProcessUnit( Component ):
  """
  Processes all incoming data from the tag array(s).
  Prevents propagation of garbage data in the case we didn't read the tag array
  """
  def construct(s, p):
    s.en        = InPort() # outputs all 0 if not enabled
    s.addr_tag  = InPort(p.bitwidth_tag)
    s.tag_array = [ InPort(p.StructTagArray) for _ in range(p.associativity) ]
    s.is_init   = InPort()
    s.hit_way   = OutPort(p.bitwidth_clog_asso)
    s.hit       = OutPort() # general hit
    s.inval_hit = OutPort() # hit on an invalid cache line that is dirty

    s.offset     = InPort(p.bitwidth_offset)
    s.wr_len     = InPort(p.bitwidth_len)
    s.word_dirty = OutPort(p.associativity) # If the word in cacheline is dirty
    s.line_dirty = OutPort(p.associativity) # If the line is dirty
    s.tag_entires= [ OutPort(p.StructTagArray) for _ in range(p.associativity) ]

    # word dirty logic
    @update
    def word_dirty_logic():
      for i in range(p.associativity):
        # moyang: this is a CIFER hack. When writing a double word (zero
        # extending a 32-bit word to a 64-bit double word), we only consider the
        # double word dirty if both 32-bit words are dirty, because we need to
        # stall the pipeline to set the two dirty bits if any of them is not
        # already dirty.
        if s.wr_len == 3:
          s.word_dirty[i] @= s.tag_array[i].dty[ s.offset[2 : p.bitwidth_offset] ] & s.tag_array[i].dty[ s.offset[2 : p.bitwidth_offset] + 1 ]
        else:
          s.word_dirty[i] @= s.tag_array[i].dty[ s.offset[2 : p.bitwidth_offset] ]

    @update
    def line_dirty_logic():
      s.line_dirty @= 0
      # OR all the wires together to see if a line is dirty
      for i in range(p.associativity):
        for j in range(p.bitwidth_dirty):
          if s.tag_array[i].dty[j] & s.en:
            s.line_dirty[i] @= y

    @update
    def comparing_logic():
      s.hit       @= n
      s.inval_hit @= n
      s.hit_way   @= 0
      if (~s.is_init) & s.en:
        for i in range(p.associativity):
          if s.tag_array[i].val == CACHE_LINE_STATE_VALID:
            if s.tag_array[i].tag == s.addr_tag:
              s.hit      @= y
              s.hit_way  @= i
          if s.line_dirty[i] & (s.tag_array[i].val == CACHE_LINE_STATE_INVALID):
            # If not valid, then we check if the line is dirty at all
            # If its dirty, then we flag the transaction as an access to a
            # partially dirty line that may require special attention
            if s.tag_array[i].tag == s.addr_tag:
              s.inval_hit @= y
              s.hit_way   @= i

    @update
    def tag_entry_output_logic():
      # Outputs what we're reading from the sram if the processing unit is
      # enabled. Otherwise we output zeros.
      for i in range(p.associativity):
        if s.en:
          s.tag_entires[i] @= s.tag_array[i]
        else:
          s.tag_entires[i] @= p.StructTagArray()

  def line_trace( s ):
    msg = f'hit:{s.hit} hit_way:{s.hit_way} inv_hit:{s.inval_hit} wr_len:{s.wr_len} word_dirty:{s.word_dirty}'
    return msg

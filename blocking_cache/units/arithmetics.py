"""
=========================================================================
arithmetic.py
=========================================================================
Combined arithmetic modules for the cache such as modified adders,
multipliers and comparators. Also include replicators

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

from pymtl3 import *
from constants.constants import *
from pymtl3.stdlib.basic_rtl   import RegEnRst, RegEn, Mux
from constants import *
from ..cache_constants import *

class DataReplicator( Component ):

  def construct( s , p ):

    s.in_    = InPort ( p.BitsData )
    s.len_   = InPort ( p.BitsLen )
    s.offset = InPort ( p.BitsOffset )
    s.amo    = InPort ()
    s.out    = OutPort( p.BitsCacheline )

    BitsLen            = p.BitsLen
    bitwidth_cacheline = p.bitwidth_cacheline
    bitwidth_data      = p.bitwidth_data
    BitsCacheline      = p.BitsCacheline
    BitsData           = p.BitsData
    bitwidth_offset    = p.bitwidth_offset
    @update
    def replicator_logic(): 
      if s.amo:
        s.out @= BitsCacheline(0)
        s.out[0:bitwidth_data] @= s.in_
      else:
        if s.len_ == BitsLen(1): 
          for i in range( 0, bitwidth_cacheline, 8 ): # byte
            s.out[i:i+8] @= s.in_[0:8]
        elif s.len_ == BitsLen(2):
          for i in range( 0, bitwidth_cacheline, 16 ): # half word
            s.out[i:i+16] @= s.in_[0:16]
        else:
          for i in range( 0, bitwidth_cacheline, bitwidth_data ):
            s.out[i:i+bitwidth_data] @= s.in_

  def line_trace( s ):
    msg = ''
    msg += f'amo:{s.is_amo} out:{s.out} '
    return msg

class DataReplicatorv2( Component ):

  def construct( s , p ):

    s.in_  = InPort ( p.BitsData )
    s.len_ = InPort ( p.BitsLen )
    s.amo  = InPort ()
    s.out  = OutPort( p.BitsCacheline )

    BitsLen            = p.BitsLen
    bitwidth_cacheline = p.bitwidth_cacheline
    bitwidth_data      = p.bitwidth_data
    BitsCacheline      = p.BitsCacheline
    BitsData           = p.BitsData

    nreplicators = clog2( p.bitwidth_data ) - 2 
    s.replications = [ Wire( p.BitsCacheline ) for i in range(nreplicators)]
    for i in range( nreplicators ):
      subwd_bitwidth = 2**(3+i)
      for j in range( 0, p.bitwidth_cacheline, subwd_bitwidth):
        s.replications[i][ j : j + subwd_bitwidth ] //= s.in_[ 0 : subwd_bitwidth ]

    ninputs = nreplicators + 1 # 1 extra for amo inputs
    s.output_mux = Mux( p.BitsCacheline, ninputs )

    for i in range( ninputs - 1 ):
      s.output_mux.in_[i+1] //= s.replications[i]
    s.output_mux.in_[0][ 0 : p.bitwidth_data] //= s.in_[ 0 : p.bitwidth_data ]
    if p.bitwidth_cacheline > p.bitwidth_data:
      s.output_mux.in_[0][ p.bitwidth_data : p.bitwidth_cacheline ] //= 0
    
    BitsSel = mk_bits( clog2(ninputs) )
    @update
    def output_mux_selection_logic():
      s.output_mux.sel @= BitsSel(0)
      if ~s.amo:
        for i in range( ninputs - 1 ):
          if s.len_ == trunc(Bits32(2**i), BitsLen):
            s.output_mux.sel @= BitsSel(i+1)
    s.out //= s.output_mux.out

  def line_trace( s ):
    msg = ''
    msg += f'i[{s.in_}] o[{s.out}] amo:{s.amo} '
    return msg

class Indexer ( Component ):

  def construct ( s, p ):

    s.index  = InPort( p.BitsIdx )
    s.offset = InPort( p.BitsAssoclog2 )
    s.out    = OutPort( p.BitsClogNlines )

    BitsClogNlines  = p.BitsClogNlines
    nblocks_per_way = p.nblocks_per_way

    @update
    def index_logic():
      s.out @= zext( s.index, BitsClogNlines ) + zext( s.offset, BitsClogNlines ) * \
        trunc( Bits32(nblocks_per_way), BitsClogNlines) 
  
  def line_trace( s ):
    msg = ""
    msg = f"idx:{s.index} off:{s.offset} "
    return msg

class Comparator( Component ):

  def construct(s, p):

    s.addr_tag  = InPort( p.BitsTag )
    s.tag_array = [ InPort( p.StructTagArray ) for _ in range( p.associativity ) ]
    s.is_init   = InPort ( Bits1 )
    s.hit       = OutPort( Bits1 )
    s.hit_way   = OutPort( p.BitsAssoclog2 )
    
    s.dirty_line = InPort( p.BitsAssoc )
    s.inval_hit  = OutPort( Bits1 )

    BitsAssoclog2 = p.BitsAssoclog2
    BitsAssoc     = p.BitsAssoc
    associativity = p.associativity

    @s.update
    def comparing_logic():
      s.hit       = n
      s.inval_hit = n
      s.hit_way   = BitsAssoclog2(0)
      if not s.is_init:
        for i in range( associativity ):
          if s.tag_array[i].val == CACHE_LINE_STATE_VALID:
            if s.tag_array[i].tag == s.addr_tag:
              s.hit = y
              s.hit_way = BitsAssoclog2(i)
          elif s.dirty_line[i]:
            # If not valid, then we check if the line is dirty at all 
            # If its dirty, then we flag the transaction as an access to a 
            # partially dirty line that may require special attention
            if s.tag_array[i].tag == s.addr_tag:
              s.inval_hit = y
              s.hit_way = BitsAssoclog2(i)
    
  def line_trace( s ):
    msg = ''
    msg += f'hit:{s.hit} hit_way:{s.hit_way} '
    return msg

class OffsetLenSelector( Component ):

  def construct(s, p):
    s.len_i    = InPort( p.BitsLen )
    s.offset_i = InPort( p.BitsOffset )
    s.is_amo   = InPort ()
    s.offset_o = OutPort( p.BitsOffset )
    s.len_o    = OutPort( p.BitsMemLen )

    BitsOffset = p.BitsOffset 
    BitsMemLen = p.BitsMemLen

    s.amo_len = Wire( p.BitsMemLen )
    if p.bitwidth_data == 32:
      s.amo_len //= 4
    else:
      s.amo_len //= lambda: zext( s.len_i, p.BitsMemLen )

    @update
    def offset_selection_logic():
      if s.is_amo:
        s.offset_o @= s.offset_i
        s.len_o    @= s.amo_len # one word read always for len
      else:
        s.offset_o @= BitsOffset(0)
        s.len_o    @= BitsMemLen(0)

class WriteBitEnGen( Component ):
  """
  Decodes the write bit enable for data array
  """
  def construct(s, p):
    s.cmd      = InPort( Bits2 ) # commmand based on what to generate
    s.dty_mask = InPort( p.BitsDirty )
    s.offset   = InPort( p.BitsOffset )     
    s.len_     = InPort( p.BitsLen )
    s.out      = OutPort( p.BitsDataWben )    

    BitsLen     = p.BitsLen
    bitwidth_nbyte = p.bitwidth_data_wben / 8
    BitsNByte   = mk_bits( bitwidth_nbyte )
    s.word_mask = Wire( BitsNByte )
    # Not used due to large area overhead
    nlens = clog2( p.bitwidth_data ) - 2 
    # @update
    # def req_word_mask_logic():
    #   s.word_mask @= 0
    #   for i in range( nlens ): 
    #     if s.len_ == BitsLen( 2**i ):
    #       s.word_mask  @= 2**( 2**(i+3) ) - 1 
          # s.out = mask << ( BitsDataWben(s.offset) << 3 )
    @update
    def req_word_mask_logic(): # smaller area
      if s.len_ == BitsLen(1):
        s.word_mask @= 0b1
      elif s.len_ == BitsLen(2):
        s.word_mask @= 0b11 
      elif s.len_ == trunc(Bits32(4), BitsLen):
        s.word_mask @= 0b1111 
      elif s.len_ == trunc(Bits32(8), BitsLen):
        s.word_mask @= 0b11111111 
      elif s.len_ == trunc(Bits32(16), BitsLen):
        s.word_mask @= 0xffff 
      else:
        s.word_mask @= 0
    
    s.shifted = Wire( BitsNByte )
    s.shifted //= lambda: s.word_mask << zext(s.offset, BitsNByte) 
    
    s.wben_req   = Wire( p.BitsDataWben )
    s.wben_dirty = Wire( p.BitsDataWben )
    bitwidth_clog_nbyte = clog2(bitwidth_nbyte)
    bitwidth_clog_dirty = clog2(p.bitwidth_dirty)
    @update
    def wben_shift_logic():
      for i in range( p.bitwidth_data_wben ):
        i_byte = trunc(Bits32(i >> 3), bitwidth_clog_nbyte)
        i_mask = trunc(Bits32(i >> 5), bitwidth_clog_dirty)
        s.wben_req[i]   @= s.shifted[ i_byte ]
        s.wben_dirty[i] @= ~(s.dty_mask[ i_mask ])
    
    BitsDataWben = p.BitsDataWben
    @update
    def output_logic():
      if s.cmd == WriteBitEnGen_CMD_REQ:
        s.out @= s.wben_req
      elif s.cmd == WriteBitEnGen_CMD_DIRTY:
        s.out @= s.wben_dirty
      else: # s.cmd == WriteBitEnGen_CMD_NONE
        s.out @= 0
    
  def line_trace( s ):
    msg = f'o[{s.out}] '
    return msg

class TagArrayRDataProcessUnit( Component ):

  def construct(s, p):
    s.en        = InPort()
    s.addr_tag  = InPort( p.BitsTag )
    s.tag_array = [ InPort( p.StructTagArray ) for _ in range( p.associativity ) ]
    s.is_init   = InPort ()
    s.hit_way   = OutPort( p.BitsAssoclog2 )
    s.hit       = OutPort() # general hit
    s.inval_hit = OutPort() # hit on an invalid cache line that is dirty
    
    s.offset     = InPort( p.BitsOffset )
    s.word_dirty = OutPort( p.BitsAssoc ) # If the word in cacheline is dirty
    s.line_dirty = OutPort( p.BitsAssoc ) # If the line is dirty
    s.tag_entires= [ OutPort( p.StructTagArray ) for _ in range( p.associativity ) ] 

    BitsAssoclog2 = p.BitsAssoclog2
    BitsAssoc     = p.BitsAssoc
    associativity = p.associativity
    bitwidth_offset = p.bitwidth_offset
    bitwidth_dirty  = p.bitwidth_dirty
    StructTagArray = p.StructTagArray

    # word dirty logic
    for i in range( associativity ):
      s.word_dirty[i] //= lambda: s.tag_array[i].dty[s.offset[2:bitwidth_offset]]

    @update
    def line_dirty_logic():
      s.line_dirty @= BitsAssoc( 0 )
      # OR all the wires together to see if a line is dirty
      for i in range( associativity ):
        for j in range( bitwidth_dirty ):
          if s.tag_array[i].dty[j] & s.en:
            s.line_dirty[i] @= y

    @update
    def comparing_logic():
      s.hit       @= n
      s.inval_hit @= n
      s.hit_way   @= BitsAssoclog2(0)
      if (~s.is_init) & s.en:
        for i in range( associativity ):
          if s.tag_array[i].val == CACHE_LINE_STATE_VALID:
            if s.tag_array[i].tag == s.addr_tag:
              s.hit      @= s.hit | y
              s.hit_way  @= BitsAssoclog2(i)
          if s.line_dirty[i] & (s.tag_array[i].val == CACHE_LINE_STATE_INVALID):
            # If not valid, then we check if the line is dirty at all 
            # If its dirty, then we flag the transaction as an access to a 
            # partially dirty line that may require special attention
            if s.tag_array[i].tag == s.addr_tag:
              s.inval_hit @= s.inval_hit | y
              s.hit_way   @= BitsAssoclog2(i)
    
    @update
    def tag_entry_output_logic():
      # Outputs what we're reading from the sram if the processing unit is 
      # enabled. Otherwise we output zeros.
      for i in range( associativity ):
        if s.en:
          s.tag_entires[i] @= s.tag_array[i]
        else:
          s.tag_entires[i] @= StructTagArray()        

  def line_trace( s ):
    msg = ''
    # msg += f't[{s.tag_array[0].tag}]'
    msg += f'hit:{s.hit} hit_way:{s.hit_way} inv_hit:{s.inval_hit} '
    return msg

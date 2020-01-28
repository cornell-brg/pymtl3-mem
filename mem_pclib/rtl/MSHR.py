"""
=========================================================================
MSHR.py
=========================================================================
Module of Miss Status Hit Register
Keeps trach of outstanding misses for the nonblocking cache

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 25 January 2020
"""
from pymtl3 import *
from mem_pclib.ifcs.MSHRMsg import mk_MSHR_msg
from mem_pclib.rtl.utils import ECompEn
from pymtl3.stdlib.ifcs.SendRecvIfc       import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.rtl.registers import RegEnRst, RegRst
from sram.SramPRTL                  import SramPRTL

class MSHR (Component):
  def construct( s,
                 MSHRMsg = "", # MSHR SRAM bitstruct

                 entries = 2, # Number of entries in MSHR
                 dbw = 32, # data
                 abw = 32, # address
                 tgw = 23, # tag
                 idw = 5,  # index
                 ofw = 4,  # offset
                 obw = 8,
                 rep = 1,
                 BitsOpaque = Bits8,
                 BitsData   = Bits32,
                 BitsOffset = Bits4,
                 BitsLen    = Bits4,
  ):
    y = wr = b1(1)
    n = rd = b1(0)
    sbw = obw + dbw + ofw + 4 + clog2(dbw//8) + rep 
    if entries == 1:
      idd = 1
    else:
      idd = clog2(entries)

    BitsTagIndex    = mk_bits( tgw + idw )    
    BitsSRAM        = mk_bits(sbw)
    BitsEntries     = mk_bits(entries)
    BitsClogEntries = mk_bits( idd )

    s.alloc_req    = RecvIfcRTL( MSHRMsg )
    s.alloc_resp   = SendIfcRTL( BitsOpaque ) 
    s.dealloc_req  = RecvIfcRTL( BitsOpaque )
    s.dealloc_resp = SendIfcRTL( MSHRMsg )

    # s.alloc_tag_index = Wire(BitsTagIndex)
    # s.alloc_tag_index //= s.alloc_req.msg.addr[ofw:abw]

    RegArrayMsg = mk_bitstruct ( f"RegArrayMsg_{entries}",{
      "val": Bits1,
      "tagidx": BitsTagIndex,
      "id": BitsClogEntries,
      "idx": BitsClogEntries,
    }, )

    SRAMMsg = mk_bitstruct( f"SRAMMsg_{entries}",{
      "opaque": BitsOpaque,
      "data"  : BitsData,
      "offset": BitsOffset,
      "type"  : Bits4,
      "len"   : BitsLen,
      "rep"   : mk_bits(rep)
    }) 

    # Register Arrays to store outstanding Misses
    s.reg_array_in  = [Wire(RegArrayMsg) for _ in range(entries)]
    s.reg_array_out = [Wire(RegArrayMsg) for _ in range(entries)]
    # s.reg_array_en  = [Wire(Bits1) for _ in range(entries)]
    s.reg_array = [RegRst(RegArrayMsg)(
      in_ = s.reg_array_in[i],
      out = s.reg_array_out[i],
      # en  = s.reg_array_en[i],
    ) for i in range(entries)]

    # MSHR Entry ID counter
    s.id_counter_in  = Wire(BitsClogEntries)
    s.id_counter_out = Wire(BitsClogEntries)
    s.id_counter = RegRst(BitsClogEntries)(
      in_ = s.id_counter_in,
      out = s.id_counter_out
    )

    # SRAM to store information on each outstanding miss
    s.MSHSRAM_val   = Wire(Bits1)
    s.MSHSRAM_type  = Wire(Bits1)
    s.MSHSRAM_idx   = Wire(BitsClogEntries)
    s.MSHSRAM_wdata = Wire(BitsSRAM)
    s.MSHSRAM_rdata = Wire(BitsSRAM)
    nbytes = int( sbw + 7 ) // 8 # $ceil(num_bits/8)
    s.MSHSRAM_wben  = Wire(mk_bits(nbytes))
    s.MSHSRAM = SramPRTL( sbw, entries )( 
      port0_val   = s.MSHSRAM_val,
      port0_type  = s.MSHSRAM_type,
      port0_idx   = s.MSHSRAM_idx,
      port0_wdata = s.MSHSRAM_wdata,
      port0_wben  = s.MSHSRAM_wben,
      port0_rdata = s.MSHSRAM_rdata,
     )
    s.MSHSRAM_wben //= mk_bits(nbytes)(-1)

    # TagIndex Comparators hooked up to each register
    # For allocation requests
    s.tag_index_match = Wire(BitsEntries)
    s.tag_index_comp = [
      ECompEn(BitsTagIndex)(
        in0 = s.reg_array_out[i].tagidx,
        in1 = s.alloc_req.msg.addr[ofw:abw],
        en  = s.reg_array_out[i].val,
        out = s.tag_index_match[i],
      ) for i in range(entries)
    ]

    # ID comparison for deallocation requests
    s.id_match = Wire(BitsEntries)
    s.id_comp = [
      ECompEn(BitsClogEntries)(
        in0 = s.reg_array_out[i].id,
        in1 = s.dealloc_req.msg[0:idd],
        en  = s.reg_array_out[i].val,
        out = s.id_match[i],
      ) for i in range(entries)
    ]    
    
    @s.update
    def id_counter_update_logic():
      s.id_counter_in = s.id_counter_out
      if s.tag_index_match != BitsEntries(0):
        s.id_counter_in = s.id_counter_out + BitsClogEntries(1)

    s.free_reg_entry = Wire(BitsClogEntries)
    @s.update
    def free_reg_array_checker():
      for i in range(entries):
        if not s.reg_array_out[i].val:
          s.free_reg_entry = BitsClogEntries(i)

    s.sram_wr_msg = Wire(SRAMMsg)  
    @s.update
    def alloc_dealloc_entries_logic():
      s.MSHSRAM_val  = n
      s.alloc_resp.msg = BitsOpaque(0)
      for i in range(entries):
        # makes sure all inputs are driven
        s.reg_array_in[i] = s.reg_array_out[i]
        
      if s.alloc_req.en:
        # INV: alloc.en would no be high unless fewer than max entries
        # alloc and no match in existing entries
        s.reg_array_in[s.free_reg_entry].val = y
        s.reg_array_in[s.free_reg_entry].tagidx =\
            s.alloc_req.msg.addr[ofw:abw]
        # Update the SRAM
        s.MSHSRAM_val  = y
        s.MSHSRAM_type = wr
        s.MSHSRAM_idx  = BitsClogEntries(i)
        s.sram_wr_msg.opaque = s.alloc_req.msg.opaque
        s.sram_wr_msg.data   = s.alloc_req.msg.data
        s.sram_wr_msg.offset = s.alloc_req.msg.addr[0:ofw]
        s.sram_wr_msg.type   = s.alloc_req.msg.type
        s.sram_wr_msg.len    = s.alloc_req.msg.len
        s.sram_wr_msg.rep    = s.alloc_req.msg.rep
        s.MSHSRAM_wdata = BitsSRAM(s.sram_wr_msg) 
        if s.tag_index_match == BitsEntries(0):
          s.reg_array_in[s.free_reg_entry].id = s.id_counter_out
          s.alloc_resp.msg = BitsOpaque(s.id_counter_out)
        else:
          for i in range(entries):
            if s.tag_index_match[i]:
              # share the same id if we have a match
              s.reg_array_in[s.free_reg_entry].id = \
                s.reg_array_out[i].id 
              s.alloc_resp.msg = BitsOpaque(s.reg_array_out[i].id)           
    
    s.MSHR_entry_count_in = Wire(BitsClogEntries)
    s.MSHR_entry_count_out = Wire(BitsClogEntries)
    s.MSHR_entry_count = RegRst(BitsClogEntries)(
      in_ = s.MSHR_entry_count_in,
      out = s.MSHR_entry_count_out
    )

    @s.update
    def entry_count_logic():
      s.MSHR_entry_count_in = s.MSHR_entry_count_out
      # Logic for incrementing counter
      if s.alloc_req.en and not s.dealloc_req.en: 
        # allocating an entry and not deallocating
        s.MSHR_entry_count_in = s.MSHR_entry_count_out + BitsClogEntries(1)
      elif not s.alloc_req.en and s.dealloc_req.en:
        # dealloc and not alloc
        s.MSHR_entry_count_in = s.MSHR_entry_count_out - BitsClogEntries(1)

    @s.update
    def alloc_dealloc_req_en_rdy_logic():
      s.alloc_req.rdy = y       
      s.dealloc_req.rdy = y
      # Keeps track of number of entries in MSHR'
      # If full, MSHR can't take alloc requests
      # If empty, no dealloc requests
      if s.MSHR_entry_count_out == entries:
        s.alloc_req.rdy = n
      elif s.MSHR_entry_count_out == 0:
        s.dealloc_req.rdy = n

    @s.update
    def alloc_resp_en_rdy_logic():
      # default rdy = yes
      s.alloc_resp.en = n
      if s.alloc_resp.rdy:
        s.alloc_resp.en = s.alloc_req.en
      

    @s.update
    def TODO_connections():

      s.dealloc_resp.en = s.dealloc_resp.rdy
      s.dealloc_resp.msg = MSHRMsg(0)

  def line_trace(s):
    msg = ''
    return msg
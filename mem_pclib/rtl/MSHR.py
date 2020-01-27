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

                 entries = 1, # Number of entries in MSHR
                 dbw = 32, # data
                 abw = 32, # address
                 tgw = 23, # tag
                 idw = 5, # index
                 ofw = 4, # offset
                 obw = 8,
                 rep = 1,
                 BitsOpaque = Bits8,
                 BitsData   = Bits32,
                 BitsOffset = Bits4,
                 BitsLen    = Bits4,
  ):
    y = b1(1)
    n = b1(0)
    sbw = obw + dbw + ofw + 4 + clog2(dbw//8) + rep 
    if entries == 1:
      idd = 1
    else:
      idd = clog2(entries)

    BitsTagIndex = mk_bits( tgw + idw )    
    BitsID       = mk_bits( idd )
    BitsSRAMIdx  = mk_bits( idd )
    BitsSRAM = mk_bits(sbw)
    BitsEntries = mk_bits(entries)

    s.alloc_req    = RecvIfcRTL( MSHRMsg )
    s.alloc_resp   = SendIfcRTL( BitsOpaque ) 
    s.dealloc_req  = RecvIfcRTL( BitsOpaque )
    s.dealloc_resp = SendIfcRTL( MSHRMsg )

    # s.alloc_tag_index = Wire(BitsTagIndex)
    # s.alloc_tag_index //= s.alloc_req.msg.addr[ofw:abw]

    RegArrayMsg = mk_bitstruct ( f"RegArrayMsg_{entries}",{
      "val": Bits1,
      "tagidx": BitsTagIndex,
      "id": BitsID,
      "idx": BitsSRAMIdx,
    }, )

    SRAMMsg = mk_bitstruct( f"SRAMMsg_{entries}",{
      "opaque": BitsOpaque,
      "data"  : BitsData,
      "offset": BitsOffset,
      "type"  : Bits4,
      "len"   : BitsLen,
      "rep"   : mk_bits(rep)
    }) 

    # MSHR Entry ID counter
    s.id_counter_in  = Wire(BitsID)
    s.id_counter_out = Wire(BitsID)
    s.id_counter = RegRst(BitsID)(
      in_ = s.id_counter_in,
      out = s.id_counter_out
    )
    @s.update
    def id_counter_update_logic():
      s.id_counter_in = s.id_counter_out
      if s.tag_index_match != b1(0):
        s.id_counter_in = s.id_counter_out + BitsID(1)

    s.free_reg_entry = Wire(BitsEntries)
    @s.update
    def free_reg_array_checker():
      for i in range(entries):
        if not s.reg_array_out[i].val:
          s.free_reg_entry = BitsEntries(i)
      

    # Register Arrays to store outstanding Misses
    s.reg_array_in  = [Wire(RegArrayMsg) for _ in range(entries)]
    s.reg_array_out = [Wire(RegArrayMsg) for _ in range(entries)]
    s.reg_array_en  = [Wire(Bits1) for _ in range(entries)]
    s.reg_array = [RegEnRst(RegArrayMsg)(
      in_ = s.reg_array_in[i],
      out = s.reg_array_out[i],
      en  = s.reg_array_en[i],
    ) for i in range(entries)]

    # TagIndex Comparators hooked up to each register
    # For allocation requests
    s.tag_index_match = [Wire(Bits1) for _ in range(entries)]
    s.tag_index_comp = [
      ECompEn(BitsTagIndex)(
        in0 = s.reg_array_out[i].tagidx,
        in1 = s.alloc_req.msg.addr[ofw:abw],
        en  = s.reg_array_out[i].val,
        out = s.tag_index_match[i],
      ) for i in range(entries)
    ]
    
    @s.update
    def tag_index_match_logic(): # logic as part of alloc
      for i in range(entries):
        if s.tag_index_match[i]:
          



    # ID comparison for deallocation requests
    s.id_match = [Wire(Bits1) for _ in range(entries)]
    s.id_comp = [
      ECompEn(BitsID)(
        in0 = s.reg_array_out[i].id,
        in1 = s.dealloc_req.msg[0:idd],
        en  = s.reg_array_out[i].val,
        out = s.id_match[i],
      ) for i in range(entries)
    ]    


    # SRAM to store information on each outstanding miss
    s.MSHSRAM_val   = Wire(Bits1)
    s.MSHSRAM_type  = Wire(Bits1)
    s.MSHSRAM_idx   = Wire(BitsSRAMIdx)
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

    # s.MSHSRAM_free_entry_in  = Wire(BitsEntries)
    # s.MSHSRAM_free_entry_out = Wire(BitsEntries)
    # s.MSHSRAM_free_entry_reg = RegRst(BitsEntries)(
    #   in_ = s.MSHSRAM_free_entry_in,
    #   out = s.MSHSRAM_free_entry_out,
    # )

    @s.update
    def TODO_connections():
      s.alloc_req.rdy = y
      s.alloc_resp.en = s.alloc_resp.rdy
      s.alloc_resp.msg = BitsOpaque(0)

      s.dealloc_req.rdy = y
      s.dealloc_resp.en = s.dealloc_resp.rdy
      s.dealloc_resp.msg = MSHRMsg(0)

  def line_trace(s):
    msg = ''
    return msg
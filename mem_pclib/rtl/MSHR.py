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
from pymtl3.stdlib.rtl.registers import RegEnRst, RegRst, Reg, RegEn
from sram.SramPRTL                  import SramPRTL
from pymtl3.stdlib.rtl.arithmetics  import Mux

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
    y = wr = dl = b1(1)
    n = rd = al = b1(0)
    len_ = clog2(dbw//8)
    sbw = ( obw + dbw + ofw + 4 + len_ + rep + 7 ) // 8 * 8
    if entries == 1:
      log_entries = 1
    else:
      log_entries = clog2(entries)
    ram = 1 + tgw + idw + log_entries 
    
    BitsCount       = mk_bits( log_entries + 1 )
    BitsClogEntries = mk_bits( log_entries )
    BitsEntries     = mk_bits( entries )
    BitsRegArray    = mk_bits( ram )
    BitsSRAM        = mk_bits( sbw )
    BitsTagIndex    = mk_bits( tgw + idw )    

    s.alloc_req    = RecvIfcRTL( MSHRMsg )
    s.alloc_resp   = SendIfcRTL( BitsOpaque ) 
    s.dealloc_req  = RecvIfcRTL( BitsOpaque )
    s.dealloc_resp = SendIfcRTL( MSHRMsg )

    # s.alloc_tag_index = Wire(BitsTagIndex)
    # s.alloc_tag_index //= s.alloc_req.msg.addr[ofw:abw]

    # RegArrayMsg = mk_bitstruct ( f"RegArrayMsg_{entries}",{
    #   "val": Bits1,
    #   "tagidx": BitsTagIndex,
    #   "id": BitsClogEntries,
    #   "idx": BitsClogEntries,
    # }, )

    # SRAMMsg = mk_bitstruct( f"SRAMMsg_{entries}",{
    #   "opaque": BitsOpaque,
    #   "data"  : BitsData,
    #   "offset": BitsOffset,
    #   "type"  : Bits4,
    #   "len"   : BitsLen,
    #   "rep"   : mk_bits(rep)
    # }) 

#--------------------------------------------------------------------
# M0 Stage
#--------------------------------------------------------------------
    # Pipeline ctrl regs
    s.val_M0 = Wire(Bits1)
    s.type_M0 = Wire(Bits1) # 0 = alloc, 1 = dealloc
    s.en_M1 = Wire(Bits1)   # for stalls in the M1 stage
    
    # Replay logic
    s.replay_in_M0 = Wire(Bits1)
    s.replay_out_M0 = Wire(Bits1)
    s.replay_reg_M0 = Reg(Bits1)(
      in_ = s.replay_in_M0,
      out = s.replay_out_M0,
    )

    s.dealloc_replay_id_in_M0  = Wire(BitsClogEntries)
    s.dealloc_replay_id_out_M0 = Wire(BitsClogEntries)
    s.dealloc_replay_id_reg_M0 = RegRst(BitsClogEntries)(
      in_ = s.dealloc_replay_id_in_M0,
      out = s.dealloc_replay_id_out_M0,
    )

    @s.update
    def alloc_dealloc_req_en_rdy_logic_M0():
      s.alloc_req.rdy = y and s.en_M1     
      s.dealloc_req.rdy = y and s.en_M1
      # Keeps track of number of entries in MSHR'
      # If full, MSHR can't take alloc requests
      # If empty, no dealloc requests
      if s.MSHR_entry_count_out == entries:
        s.alloc_req.rdy = n
      elif s.MSHR_entry_count_out == 0 or s.alloc_req.en:
        s.dealloc_req.rdy = n
      if s.replay_out_M0:
        s.dealloc_req.rdy = n
        s.alloc_req.rdy = n
    
    @s.update
    def ctrl_signals_logic_M0():
      # TODO TESTING condition only remove the if condition and 
      # replace with below
      s.val_M0 = n # default no
      if s.dealloc_req.msg != BitsOpaque(-1):
        s.val_M0 = s.alloc_req.en or s.dealloc_req.en or s.replay_out_M0
      if s.replay_out_M0:
        s.val_M0 = s.val_M0 or y

      # s.val_M0 = s.alloc_req.en or s.dealloc_req.en or s.id_match>1
      s.type_M0 = b1(0) if s.alloc_req.en else b1(1)

    # SRAM to store information on each outstanding miss
    s.MSHSRAM_val   = Wire(Bits1)
    s.MSHSRAM_type  = Wire(Bits1)
    s.MSHSRAM_idx   = Wire(BitsClogEntries)
    s.MSHSRAM_wdata = Wire(BitsSRAM)

    # Register Arrays to store outstanding Misses
    s.reg_array_in  = [Wire(BitsRegArray) for _ in range(entries)]
    s.reg_array_out = [Wire(BitsRegArray) for _ in range(entries)]
    s.reg_array = [RegRst(BitsRegArray)(
      in_ = s.reg_array_in[i],
      out = s.reg_array_out[i],
    ) for i in range(entries)]

    s.reg_val_in      = Wire(BitsEntries)
    s.reg_tagIdx_in   = [Wire(BitsTagIndex) for _ in range(entries)]
    s.reg_id_in       = [Wire(BitsClogEntries) for _ in range(entries)]
    s.reg_val_out     = Wire(BitsEntries)
    s.reg_tagIdx_out  = [Wire(BitsTagIndex) for _ in range(entries)]
    s.reg_id_out      = [Wire(BitsClogEntries) for _ in range(entries)]

    for i in range(entries):
      s.reg_val_out[i]    //= s.reg_array_out[i][0]
      s.reg_tagIdx_out[i] //= s.reg_array_out[i][1:1+tgw+idw]
      s.reg_id_out[i]     //= s.reg_array_out[i][1+tgw+idw:1+tgw+idw+log_entries]
      s.reg_array_in[i][0] //= s.reg_val_in[i]
      s.reg_array_in[i][1:1+tgw+idw] //= s.reg_tagIdx_in[i]
      s.reg_array_in[i][1+tgw+idw:1+tgw+idw+log_entries] //= s.reg_id_in[i] 

    # comparator enable logic
    s.id_comp_en_M0 = Wire(BitsEntries)
    s.tag_index_comp_en_M0 = Wire(BitsEntries)
    @s.update
    def comparator_en_logic_M0():
      for i in range(entries):
        s.id_comp_en_M0[i] = s.reg_val_out[i] and s.val_M0
        s.tag_index_comp_en_M0[i] = s.reg_val_out[i] and s.val_M0
    # TagIndex Comparators hooked up to each register
    # For allocation requests
    s.tag_index_match = Wire(BitsEntries)
    s.tag_index_comp = [
      ECompEn(BitsTagIndex)(
        in0 = s.reg_tagIdx_out[i], # tagIdx
        in1 = s.alloc_req.msg.addr[ofw:abw],
        en  = s.tag_index_comp_en_M0[i], # val
        out = s.tag_index_match[i],
      ) for i in range(entries)
    ]
    # mux for choosing the correct id to use in case 
    # of a replay
    s.dealloc_id_M0 = Wire(BitsClogEntries)
    s.id_mux = Mux(BitsClogEntries, 2)(
      in_ = {
        0: s.dealloc_req.msg[0:log_entries],
        1: s.dealloc_replay_id_out_M0,
      },
      sel = s.replay_out_M0,
      out = s.dealloc_id_M0,
    )
    # ID comparison for deallocation requests
    s.id_match = Wire(BitsEntries)
    s.id_comp = [
      ECompEn(BitsClogEntries)(
        in0 = s.reg_id_out[i], # id
        in1 = s.dealloc_id_M0,
        en  = s.id_comp_en_M0[i], # val
        out = s.id_match[i],
      ) for i in range(entries)
    ]    
    
    # MSHR Entry ID counter
    s.id_counter_in  = Wire(BitsClogEntries)
    s.id_counter_out = Wire(BitsClogEntries)
    s.id_counter = RegRst(BitsClogEntries)(
      in_ = s.id_counter_in,
      out = s.id_counter_out
    )
    @s.update
    def id_counter_update_logic():
      s.id_counter_in = s.id_counter_out
      if s.val_M0 and s.type_M0 == al:
        if s.tag_index_match == BitsEntries(0):
          # increment if no match
          s.id_counter_in = s.id_counter_out + BitsClogEntries(1)

    # Checks for free entries
    s.free_reg_entry = Wire(BitsClogEntries)
    @s.update
    def free_reg_array_checker():
      if s.val_M0:
        for i in range(entries):
          if not s.reg_val_out[i]: # check for free entries in reg array
            s.free_reg_entry = BitsClogEntries(i)

    # Count of free MSHR Entries
    s.MSHR_entry_count_in = Wire(BitsCount)
    s.MSHR_entry_count_out = Wire(BitsCount)
    s.MSHR_entry_count = RegRst(BitsCount)(
      in_ = s.MSHR_entry_count_in,
      out = s.MSHR_entry_count_out
    )
    @s.update
    def entry_count_logic():
      # Logic for incrementing counter
      s.MSHR_entry_count_in = s.MSHR_entry_count_out
      if s.val_M0:
        if s.type_M0 == al: 
          # allocating an entry
          s.MSHR_entry_count_in = s.MSHR_entry_count_out + BitsCount(1)
        elif s.type_M0 == dl:
          # dealloc and not alloc
          s.MSHR_entry_count_in = s.MSHR_entry_count_out - BitsCount(1)

    s.alloc_resp_M0 = Wire(BitsOpaque)
    s.dealloc_tagIdx_M0 = Wire(BitsTagIndex)
    @s.update
    def alloc_dealloc_entries_logic():
      # defaults
      s.MSHSRAM_val  = n
      s.alloc_resp_M0 = BitsOpaque(0)
      s.dealloc_replay_id_in_M0 = s.dealloc_replay_id_out_M0
      s.replay_in_M0 = n
      # s.num_id_match_M0 = BitsCount(0)
      for i in range(entries):
        # makes sure all inputs are driven
        s.reg_val_in[i]    = s.reg_val_out[i]
        s.reg_tagIdx_in[i] = s.reg_tagIdx_out[i]
        s.reg_id_in[i]     = s.reg_id_out[i]

      if s.val_M0:
        if s.type_M0 == al:
          # Invariant: alloc.en would not be high unless fewer than max entries
          # alloc and no match in existing entries
          s.reg_val_in[s.free_reg_entry] = y
          s.reg_tagIdx_in[s.free_reg_entry] = s.alloc_req.msg.addr[ofw:abw]
          # Update the SRAM
          s.MSHSRAM_val  = y
          s.MSHSRAM_type = wr
          s.MSHSRAM_idx  = BitsClogEntries(s.free_reg_entry)
          s.MSHSRAM_wdata[0:obw]       = s.alloc_req.msg.opaque
          s.MSHSRAM_wdata[obw:obw+dbw] = s.alloc_req.msg.data
          s.MSHSRAM_wdata[obw+dbw:obw+dbw+ofw] = s.alloc_req.msg.addr[0:ofw]
          s.MSHSRAM_wdata[obw+dbw+ofw:obw+dbw+ofw+4]   = s.alloc_req.msg.type
          s.MSHSRAM_wdata[obw+dbw+ofw+4:obw+dbw+ofw+4+len_] = s.alloc_req.msg.len
          s.MSHSRAM_wdata[obw+dbw+ofw+4+len_:obw+dbw+ofw+4+len_+rep] = s.alloc_req.msg.rep
          # s.MSHSRAM_wdata = BitsSRAM(s.sram_wr_msg) 
          if s.tag_index_match == BitsEntries(0):
            # If no matching tag index (no misses to same cache line), 
            # then we use a new id
            s.reg_id_in[s.free_reg_entry] = s.id_counter_out
            s.alloc_resp_M0 = BitsOpaque(s.id_counter_out)
          else:
            # If we have a miss to the same cache line, then we will find the
            # id of the matching cache line and use that id for this new entry
            # since we a miss to the same cache line 
            for i in range(entries):
              if s.tag_index_match[i]:
                # share the same id if we have a match and return the same id
                s.reg_id_in[s.free_reg_entry] = s.reg_id_out[i] 
                s.alloc_resp_M0 = BitsOpaque(s.reg_id_out[i])      
        elif s.type_M0 == dl:
          # If we have dealloc, then we will first find matching tagIndex is the
          # reg arrays and dealloc these entries and send them out
          index = 0
          count = 0
          for i in range(entries): # check for matches in reg array
            # Invariant: id must exist in reg array
            if s.id_match[i]:
              # Undefined action if id does not match...
              # We can always assume it matches since we will always alloc 
              # before dealloc 
              index = i # we found the matching index
              count += 1
          # print(count)
          # s.num_id_match_M0 = BitsCount(count)
          if count > 1:
            s.replay_in_M0 = y
            if not s.replay_out_M0:
              s.dealloc_replay_id_in_M0 = s.dealloc_req.msg[0:log_entries]            

          s.reg_val_in[index] = n # invalidate current entry
          s.dealloc_tagIdx_M0 = s.reg_tagIdx_out[index] # pass tagIndex for rebuild
          s.MSHSRAM_val = y
          s.MSHSRAM_type = rd
          s.MSHSRAM_idx  = BitsClogEntries(index)
        

    nbytes = int( sbw + 7 ) // 8 # $ceil(num_bits/8)
    s.MSHSRAM_wben  = Wire(mk_bits(nbytes))
    s.MSHSRAM_out   = Wire(BitsSRAM)
    s.MSHSRAM_rdata = Wire(BitsSRAM)
    s.MSHSRAM = SramPRTL( sbw, entries )( 
      port0_val   = s.MSHSRAM_val,
      port0_type  = s.MSHSRAM_type,
      port0_idx   = s.MSHSRAM_idx,
      port0_wdata = s.MSHSRAM_wdata,
      port0_wben  = s.MSHSRAM_wben,
      port0_rdata = s.MSHSRAM_out,
     )
    s.MSHSRAM_wben //= mk_bits(nbytes)(-1) # always write to all bytes in sram
#--------------------------------------------------------------------
# M1 Stage
#--------------------------------------------------------------------
    s.ostall_M1 = Wire(Bits1)
    s.is_stall_M1 = Wire(Bits1)
    s.is_stall_reg_M1 = RegRst(Bits1)(
      in_ = s.ostall_M1,
      out = s.is_stall_M1,
    )
    s.MSHSRAM_rdata_stalled = Wire(BitsSRAM)
    s.stall_reg_en_M1 = Wire(Bits1)
    s.stall_reg_M1 = RegEn( BitsSRAM )( # Saves output of the SRAM during stall
        en  = s.stall_reg_en_M1,               # which is only saved for 1 cycle
        in_ = s.MSHSRAM_out,
        out = s.MSHSRAM_rdata_stalled 
      ) 
    s.stall_mux_sel_M1 = Wire(Bits1)
    s.stall_mux_M1 = Mux( BitsSRAM, 2 )(
      in_ = {
        0: s.MSHSRAM_out,
        1: s.MSHSRAM_rdata_stalled 
      },
      sel = s.stall_mux_sel_M1,
      out = s.MSHSRAM_rdata,
    )
    @s.update
    def stall_logic_M1():
      s.stall_mux_sel_M1 = s.is_stall_M1
      s.stall_reg_en_M1  = not s.is_stall_M1 

    # Pipline regs
    s.alloc_resp_M1 = Wire(BitsOpaque)
    
    s.alloc_resp_reg_M1 = RegEnRst(BitsOpaque)(
      in_ = s.alloc_resp_M0,
      out = s.alloc_resp_M1, 
      en  = s.en_M1,
    )
    # alloc resp here
    s.alloc_resp.msg //= s.alloc_resp_M1
    
    s.val_M1 = Wire(Bits1)
    s.val_reg_M1 = RegEnRst(Bits1)(
      in_ = s.val_M0,
      out = s.val_M1,
      en  = s.en_M1,
    )

    s.type_M1 = Wire(Bits1) # 0 = alloc, 1 = dealloc
    s.type_reg_M1 = RegEnRst(Bits1)(
      in_ = s.type_M0,
      out = s.type_M1,
      en  = s.en_M1,
    )

    s.dealloc_tagIdx_M1 = Wire(BitsTagIndex)
    s.dealloc_tagIdx_reg_M1 = RegEnRst(BitsTagIndex)(
      in_ = s.dealloc_tagIdx_M0,
      out = s.dealloc_tagIdx_M1,
      en = s.en_M1,
    )

    @s.update
    def alloc_dealloc_resp_en_rdy_logic_M1():
      # default rdy = n
      s.alloc_resp.en = n
      s.dealloc_resp.en = n
      s.en_M1 = y
      if s.val_M1:
        if s.alloc_resp.rdy and s.type_M1 == al:
          s.alloc_resp.en = y
        elif s.dealloc_resp.rdy and s.type_M1 == dl:
          s.dealloc_resp.en = y
        else:
          s.en_M1 = n 
      s.ostall_M1 = ~s.en_M1

    @s.update
    def dealloc_resp_logic_M1():
      s.dealloc_resp.msg = MSHRMsg(0,0,0,0,0,0)
      if s.val_M1:
        # put together the dealloc response
        s.dealloc_resp.msg.opaque = s.MSHSRAM_rdata[0:obw]
        s.dealloc_resp.msg.data = s.MSHSRAM_rdata[obw:obw+dbw]
        s.dealloc_resp.msg.addr[0:ofw] = s.MSHSRAM_rdata[obw+dbw:obw+dbw+ofw]
        s.dealloc_resp.msg.type = s.MSHSRAM_rdata[obw+dbw+ofw:obw+dbw+ofw+4]
        s.dealloc_resp.msg.len = s.MSHSRAM_rdata[obw+dbw+ofw+4:obw+dbw+ofw+4+len_]
        s.dealloc_resp.msg.rep = s.MSHSRAM_rdata[obw+dbw+ofw+4+len_:obw+dbw+ofw+4+len_+rep]
        s.dealloc_resp.msg.addr[ofw:abw] = s.dealloc_tagIdx_M1

  def line_trace(s):
    types = ['al', 'dl']
    msg_M0 = "  "
    if s.val_M0:
      msg_M0 = types[s.type_M0]
    
    msg_M1 = "  "
    if s.val_M1:
      msg_M1 = types[s.type_M1]
    
    pipeline = f"{msg_M0}|{msg_M1}"

    msg = ' '
    msg += f' reg[{s.reg_array_out[0]},{s.reg_array_out[1]},'
    msg += f' {s.reg_array_out[2]},{s.reg_array_out[3]}]'
    msg += f' S[{s.MSHSRAM_out}]'
    msg += f' St[{s.MSHSRAM_rdata}]'
    # msg += ' tgid_m[{:b}]'.format(int(s.tag_index_match))
    # msg += ' id_m[{:4b}]'.format(int(s.id_match))
    # msg += f' rly[{s.replay_out_M0}]'
    msg += f' e={s.en_M1}'
    return pipeline + msg
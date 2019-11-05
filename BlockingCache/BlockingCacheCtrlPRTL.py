"""
=========================================================================
 BlockingCacheCtrlPRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Control 

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 04 November 2019
"""
import random

from pymtl3      import *
from pymtl3.stdlib.rtl.registers import RegEnRst, RegRst
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from pymtl3.stdlib.rtl.arithmetics import LShifter
# Constants

STATE_GO           = b3(0)
STATE_REFILL       = b3(1)
STATE_EVICT        = b3(2)
STATE_REFILL_WRITE = b3(3)
STATE_WRITE        = b3(4)

wr = y = b1(1)
rd = n = x = b1(0)

class BlockingCacheCtrlPRTL ( Component ):
  def construct( s,
                 dbw           = 32,       # 
                 ofw           = 4,        # offset bitwidth
                 BitsAddr      = "inv",    # address bitstruct
                 BitsOpaque    = "inv",    # opaque 
                 BitsType      = "inv",    # type
                 BitsData      = "inv",    # data 
                 BitsCacheline = "inv",    # cacheline 
                 BitsIdx       = "inv",    # index 
                 BitsTag       = "inv",    # tag 
                 BitsOffset    = "inv",    # offset 
                 BitsTagWben   = "inv",    # Tag array write byte enable
                 BitsDataWben  = "inv",    # Data array write byte enable
                 BitsRdDataMux = "inv",    # Read data mux M2 
                 twb           = 4,        # Tag array write byte enable bitwidth
                 dwb           = 16,       # Data array write byte enable bitwidth
                 rmx2          = 3,        # Read word mux bitwidth
  ):
    
    
    mxsel0 = BitsRdDataMux(0)
    wben0 = BitsDataWben(0)
    wbenf = BitsDataWben(-1)
    tg_wbenf = BitsTagWben(-1)
    data_array_wb_mask = 2**(dbw//8)-1
    READ  = BitsType(MemMsgType.READ)
    WRITE = BitsType(MemMsgType.WRITE)
    INIT  = BitsType(MemMsgType.WRITE_INIT)
    
    #-------------------------------------------------------------------
    # Interface
    #-------------------------------------------------------------------
    
    s.cachereq_en   = InPort(Bits1)
    s.cachereq_rdy  = OutPort(Bits1)

    s.cacheresp_en  = OutPort(Bits1)
    s.cacheresp_rdy = InPort(Bits1) 

    s.memreq_en     = OutPort(Bits1)
    s.memreq_rdy    = InPort(Bits1)

    s.memresp_en    = InPort(Bits1)
    s.memresp_rdy   = OutPort(Bits1)
    
    #--------------------------------------------------------------------
    # M0 Ctrl Signals 
    #--------------------------------------------------------------------
    
    s.cachereq_type_M0    = InPort (BitsType)
    s.memresp_mux_sel_M0  = OutPort(Bits1)
    s.wdata_mux_sel_M0    = OutPort(Bits2)
    s.tag_array_val_M0    = OutPort(Bits1)
    s.tag_array_type_M0   = OutPort(Bits1)
    s.tag_array_wben_M0   = OutPort(BitsTagWben) 
    s.ctrl_bit_val_wr_M0  = OutPort(Bits1)
    s.ctrl_bit_dty_wr_M0  = OutPort(Bits1)
    s.reg_en_M0           = OutPort(Bits1)
    s.MSHR_type           = InPort (BitsType)   
 
    #-------------------------------------------------------------------
    # M1 Ctrl Signals
    #-------------------------------------------------------------------
    
    s.cachereq_type_M1   = InPort(BitsType)
    s.ctrl_bit_val_rd_M1 = InPort(Bits1)
    s.ctrl_bit_dty_rd_M1 = InPort(Bits1)
    s.tag_match_M1       = InPort(Bits1)
    s.offset_M1          = InPort(BitsOffset)
    s.reg_en_M1          = OutPort(Bits1)
    s.data_array_val_M1  = OutPort(Bits1)
    s.data_array_type_M1 = OutPort(Bits1)
    s.data_array_wben_M1 = OutPort(BitsDataWben)
    s.reg_en_MSHR        = OutPort(Bits1) 

    #------------------------------------------------------------------
    # M2 Ctrl Signals
    #------------------------------------------------------------------
    
    s.cachereq_type_M2      = InPort(BitsType)
    s.offset_M2             = InPort(BitsOffset)
    s.reg_en_M2             = OutPort(Bits1)
    s.read_data_mux_sel_M2  = OutPort(mk_bits(clog2(2)))
    s.read_word_mux_sel_M2  = OutPort(BitsRdDataMux)
    # Output Signals
    s.hit_M2                = OutPort(Bits2)
    s.memreq_type           = OutPort(BitsType)    
    
    #------------------------------------------------------------------
    # Connection Wires
    #------------------------------------------------------------------
    s.is_refill_M0 = Wire(Bits1)
    s.is_refill_M1 = Wire(Bits1)
    s.is_refill_M2 = Wire(Bits1)
    s.hit_M1 = Wire(Bits1)
    
    #------------------------------------------------------------------
    # Stall and Ostall Signals
    #------------------------------------------------------------------
    
    s.stall_M0  = Wire(Bits1)    
    s.stall_M1  = Wire(Bits1)    
    s.stall_M2  = Wire(Bits1)    
    s.ostall_M0 = Wire(Bits1)
    s.ostall_M1 = Wire(Bits1)
    s.ostall_M2 = Wire(Bits1)

    #------------------------------------------------------------------
    # Cache-wide FSM
    #------------------------------------------------------------------
    # FSM to control refill and evict tranaction conditions. 
    s.curr_state = Wire(Bits3)
    s.next_state = Wire(Bits3)
    s.state_transition_block = RegRst(Bits3, STATE_GO)(
      out = s.curr_state,
      in_ = s.next_state
    )
    # FSM STATGE TRANSITION LIVES IN M1 stage but affects behavior in other stage
    # We should not change the FSM stage from any other stage
    @s.update 
    def next_state_block():
      s.next_state = STATE_GO
      if s.curr_state == STATE_GO:
        if s.cachereq_type_M1 != INIT:
          if s.val_M1 and ~s.is_refill_M1:
            if s.cachereq_type_M0 == WRITE:           s.next_state = STATE_WRITE  # M0 transition
            if   ~s.hit_M1 and s.ctrl_bit_dty_rd_M1:  s.next_state = STATE_EVICT  # M1 transition
            elif ~s.hit_M1 and ~s.ctrl_bit_dty_rd_M1: s.next_state = STATE_REFILL # M1 transistion

      elif s.curr_state == STATE_REFILL:
        if s.is_refill_M0 and s.MSHR_type == WRITE:   s.next_state = STATE_REFILL_WRITE
        elif s.is_refill_M0:                          s.next_state = STATE_GO
        else:                                         s.next_state = STATE_REFILL
      elif s.curr_state == STATE_EVICT:               s.next_state = STATE_REFILL
      elif s.curr_state == STATE_WRITE:               
        if   ~s.hit_M1 and s.ctrl_bit_dty_rd_M1:      s.next_state = STATE_EVICT  # M1 transition
        elif ~s.hit_M1 and ~s.ctrl_bit_dty_rd_M1:     s.next_state = STATE_REFILL # M1 transition
        elif  s.hit_M1 and ~s.ctrl_bit_dty_rd_M1:     s.next_state = STATE_GO     # M1 transition - return to normal 
        
        s.next_state = STATE_GO
      elif s.curr_state == STATE_REFILL_WRITE:      s.next_state = STATE_GO
      else:
        assert False, 'undefined state: next state block'

    #--------------------------------------------------------------------
    # Y Stage 
    #--------------------------------------------------------------------
    @s.update
    def mem_resp_rdy():
      if s.curr_state == STATE_REFILL:      
        s.memresp_rdy = b1(1)
      else:
        s.memresp_rdy = b1(0)    

    #--------------------------------------------------------------------
    # M0 Stage 
    #--------------------------------------------------------------------
    
    s.val_M0 = Wire(Bits1)
    s.is_write_refill_M0 = Wire(Bits1)

    s.is_refill_reg_M0 = RegRst(Bits1)\
    ( #NO STALLS should occur while refilling
      in_ = s.memresp_en,
      out = s.is_refill_M0
    )


    CS_tag_array_wben_M0  = slice( 7, 7 + twb )
    CS_wdata_mux_sel_M0   = slice( 5, 7 ) 
    CS_memresp_mux_sel_M0 = slice( 4, 5 )
    CS_tag_array_type_M0  = slice( 3, 4 )
    CS_tag_array_val_M0   = slice( 2, 3 )
    CS_ctrl_bit_dty_wr_M0 = slice( 1, 2 )
    CS_ctrl_bit_val_wr_M0 = slice( 0, 1 )

    s.cs0 = Wire( mk_bits( 7 + twb ) ) # Bits for control signal table
   
    @s.update
    def is_write_refill():
      if s.curr_state == STATE_REFILL_WRITE:
        s.is_write_refill_M0 = y
      else:
        s.is_write_refill_M0 = n
 
    @s.update
    def stall_logic_M0():
      s.ostall_M0 = b1(0)  # Not sure if neccessary but include for completeness
      s.cachereq_rdy = (~s.stall_M1 and s.curr_state == STATE_GO) and s.next_state != STATE_REFILL \
                          and s.curr_state != STATE_REFILL_WRITE
      
    @s.update
    def comb_block_M0(): # logic block for setting output ports
      s.val_M0 = s.cachereq_en or s.is_refill_M0 or s.is_write_refill_M0
      s.reg_en_M0 = s.memresp_en
      #               tag_wben|wd_mux|mr_mux|tg_ty|tg_v|dty|val
      s.cs0 = concat( tg_wbenf, b2(0), b1(0),  rd ,  n , n , n )
      if s.val_M0: #                                          tag_wben|wd_mux|mr_mux|tg_ty|tg_v|dty|val
        if s.is_refill_M0:                    s.cs0 = concat( tg_wbenf, b2(1), b1(1),  wr ,  y , n , y )    
        elif s.is_write_refill_M0:            s.cs0 = concat( tg_wbenf, b2(2), b1(1),  wr ,  y , y , y ) 
        else:
          if (s.cachereq_type_M0 == INIT):    s.cs0 = concat( tg_wbenf, b2(0), b1(0),  wr ,  y , n , y )
          elif (s.cachereq_type_M0 == READ):  s.cs0 = concat( tg_wbenf, b2(0), b1(0),  rd ,  y , n , n )
          elif (s.cachereq_type_M0 == WRITE): s.cs0 = concat( tg_wbenf, b2(0), b1(0),  rd ,  y , n , n )

      s.tag_array_type_M0  = s.cs0[ CS_tag_array_type_M0  ]
      s.tag_array_val_M0   = s.cs0[ CS_tag_array_val_M0   ]
      s.tag_array_wben_M0  = s.cs0[ CS_tag_array_wben_M0  ]
      s.wdata_mux_sel_M0   = s.cs0[ CS_wdata_mux_sel_M0   ]
      s.memresp_mux_sel_M0 = s.cs0[ CS_memresp_mux_sel_M0 ]
      s.ctrl_bit_dty_wr_M0 = s.cs0[ CS_ctrl_bit_dty_wr_M0 ]
      s.ctrl_bit_val_wr_M0 = s.cs0[ CS_ctrl_bit_val_wr_M0 ]

    #--------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------
    s.val_M1 = Wire(Bits1)
    s.is_write_refill_M1 = Wire(Bits1)

    s.val_reg_M1 = RegEnRst(Bits1)\
    (
      en  = s.reg_en_M1,
      in_ = s.val_M0,
      out = s.val_M1,
    )

    s.is_refill_reg_M1 = RegRst(Bits1)\
    (
      in_ = s.is_refill_M0,
      out = s.is_refill_M1
    )

    s.is_write_refill_reg_M1 = RegRst(Bits1)\
    (
      in_ = s.is_write_refill_M0,
      out = s.is_write_refill_M1
    )

    @s.update
    def hit_logic_M1():
      s.hit_M1 = s.tag_match_M1 and s.ctrl_bit_val_rd_M1 \
                 and s.cachereq_type_M1 != INIT or s.is_write_refill_M1 
      s.hit_M2[1]= b1(0)
    
    # Calculating shift amount
    # 0 -> 0x000f, 1 -> 0x00f0, 2 -> 0x0f00, 3 -> 0xf000 
    s.shamt          = Wire(mk_bits(clog2(dwb)))
    s.shamt[0:2]   //= b2(0)
    s.shamt[2:ofw] //= s.offset_M1
    s.wben_out = Wire(BitsDataWben)
    s.wben_in  = Wire(BitsDataWben)
    s.WbenGen = LShifter( BitsDataWben, clog2(dwb) )(
      in_ = s.wben_in,
      shamt = s.shamt,
      out = s.wben_out
    )

    @s.update 
    def en_MSHR(): # TEMPORARY; NOT SURE WHAT TO DO WITH THAT SIGNAL YET
      if not s.hit_M1 and not s.curr_state == STATE_REFILL:
        s.reg_en_MSHR = b1(1)
      else:
        s.reg_en_MSHR = b1(0)

    @s.update
    def en_M1():
      s.reg_en_M1 = ~s.stall_M1

    CS_data_array_wben_M1   = slice( 3,  3 + dwb )
    CS_data_array_type_M1   = slice( 2,  3 )
    CS_data_array_val_M1    = slice( 1,  2 )
    CS_ostall_M1            = slice( 0,  1 )
    
    s.cs1 = Wire( mk_bits( 3 + dwb ) )

    @s.update
    def comb_block_M1(): 
      s.wben_in = BitsDataWben(data_array_wb_mask)
      wben = s.wben_out
      #               wben| ty|val|ost
      s.cs1 = concat(wben0, x , n , n)
      if s.val_M1: #                                                wben| ty|val|ost
        if s.is_refill_M1:                          s.cs1 = concat(wbenf, wr, y , n )
        else:      
          if s.cachereq_type_M1 == INIT:            s.cs1 = concat( wben, wr, y , n )
          elif ~s.hit_M1 and ~s.ctrl_bit_dty_rd_M1: s.cs1 = concat(wben0, x , n , n )
          elif ~s.hit_M1 and  s.ctrl_bit_dty_rd_M1: s.cs1 = concat(wben0, x , n , n ) #TODO
          elif  s.hit_M1 and ~s.ctrl_bit_dty_rd_M1:
            if   s.cachereq_type_M1 == READ:        s.cs1 = concat(wben0, rd, y , n ) 
            elif s.cachereq_type_M1 == WRITE:       s.cs1 = concat( wben, wr, y , n)
            else:                                   s.cs1 = concat(wben0, x , n , n)
          elif  s.hit_M1 and  s.ctrl_bit_dty_rd_M1:
            if   s.cachereq_type_M1 == READ:        s.cs1 = concat(wben0, rd, y , n)
            elif s.cachereq_type_M1 == WRITE:       s.cs1 = concat( wben, wr, y , n)
      s.data_array_type_M1        = s.cs1[ CS_data_array_type_M1 ]
      s.data_array_val_M1         = s.cs1[ CS_data_array_val_M1  ]
      s.data_array_wben_M1        = s.cs1[ CS_data_array_wben_M1 ]   
      s.ostall_M1                 = s.cs1[ CS_ostall_M1          ]   
      s.stall_M1 = s.ostall_M1 or s.ostall_M1   

    #-----------------------------------------------------
    # M2 Stage 
    #-----------------------------------------------------
    s.val_M2 = Wire(Bits1)
    s.is_write_refill_M2 = Wire(Bits1)

    s.val_reg_M2 = RegEnRst(Bits1)\
    (
      en  = s.reg_en_M2,
      in_ = s.val_M1,
      out = s.val_M2,
    )

    s.hit_reg_M2 = RegEnRst(Bits1)\
    (
      en  = s.reg_en_M2,
      in_ = s.hit_M1,
      out = s.hit_M2[0]
    )

    s.is_refill_reg_M2 = RegRst(Bits1)\
    (
      in_ = s.is_refill_M1,
      out = s.is_refill_M2
    )

    s.is_write_refill_reg_M2 = RegRst(Bits1)\
    (
      in_ = s.is_write_refill_M1,
      out = s.is_write_refill_M2
    )
    @s.update
    def en_M2():
      s.reg_en_M2 = ~s.stall_M2

    CS_read_word_mux_sel_M2 = slice( 8,  8 + rmx2 )
    CS_read_data_mux_sel_M2 = slice( 7,  8 )
    CS_ostall_M2            = slice( 6,  7 )
    CS_memreq_type          = slice( 2,  6 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )
    s.cs2 = Wire( mk_bits( 8 + rmx2 ) )
    s.msel = Wire(BitsRdDataMux)
    @s.update
    def comb_block_M2(): # comb logic block and setting output ports
      s.msel = BitsRdDataMux(s.offset_M2) + BitsRdDataMux(1)  
      #            word_mux|rdata_mux|ostall|memreq_type|memreq|cacheresp  
      s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     n   )
      if s.val_M2:                                     #  word_mux|rdata_mux|ostall|memreq_type|memreq|cacheresp  
        if ~s.memreq_rdy or ~s.cacheresp_rdy:s.cs2 = concat(mxsel0,   b1(0) ,  y   ,   READ    ,    n ,     y   ) # STALL
        elif s.is_refill_M2:                   
          if s.cachereq_type_M2 == READ:     s.cs2 = concat(s.msel,   b1(1) ,  n   ,   READ    ,    n ,     y   )
          elif s.cachereq_type_M2 == WRITE:  s.cs2 = concat(mxsel0,   b1(1) ,  n   ,   READ    ,    n ,     y   )
        else:
          if s.cachereq_type_M2 == INIT:     s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     y   )
          elif s.cachereq_type_M2 == READ:
            if s.hit_M2[0]:                  s.cs2 = concat(s.msel,   b1(0) ,  n   ,   READ    ,    n ,     y   )
            else:                            s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    y ,     n   )
          elif s.cachereq_type_M2 == WRITE:# and s.curr_state != STATE_WRITE
            if s.is_write_refill_M2:         s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     n   )
            elif s.hit_M2[0]:                s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     y   )
        
      s.memreq_en                 = s.cs2[ CS_memreq_en            ]
      s.cacheresp_en              = s.cs2[ CS_cacheresp_en         ] 
      s.read_word_mux_sel_M2      = s.cs2[ CS_read_word_mux_sel_M2 ]
      s.read_data_mux_sel_M2      = s.cs2[ CS_read_data_mux_sel_M2 ]
      s.memreq_type               = s.cs2[ CS_memreq_type          ]
      s.ostall_M2                 = s.cs2[ CS_ostall_M2            ]
      s.stall_M2  = s.ostall_M2


  def line_trace( s ):
    colors = {'RED': '\033[91m', 'GREEN': '\033[92m', 'WHITE': '\033[0m'}
    types = ["rd","wr","in"]
    if s.is_refill_M0 and s.val_M0 and s.cachereq_rdy: 
      msg_M0 = "rf" 
    elif s.is_refill_M0 and s.val_M0 and not s.cachereq_rdy:
      msg_M0 = "#r" 
    else:
      if s.val_M0 and s.curr_state == STATE_REFILL_WRITE:
        msg_M0 = "wf"
      elif s.val_M0:
        msg_M0 = types[s.cachereq_type_M0]  
      elif not s.cachereq_rdy:
        msg_M0 = "# "
      else: 
        msg_M0 = "  "
    if s.val_M1:
      if s.is_refill_M1:
        msg_M1 = "rf" 
      elif ~s.hit_M1 and s.cachereq_type_M1 != 2: 
        msg_M1 = colors['RED'] + types[s.cachereq_type_M1] + colors['WHITE']
      else: 
        msg_M1 = types[s.cachereq_type_M1]
    else:
      msg_M1 = "  "
    msg_M2 = "rf" if s.is_refill_M2 and s.val_M2 else types[s.cachereq_type_M2] if s.val_M2 else "  "
    msg_memresp = ">" if s.memresp_en else " "
    msg_memreq = ">" if s.memreq_en else " "    

    states = ["Go","Rf","Ev","Wf","Wr"]
    msg_state = states[s.curr_state]  
    stage1 = "{}|{}".format(msg_memresp,msg_M0) if s.curr_state == STATE_REFILL and \
      s.memresp_en else "  {}".format(msg_M0)
    stage2 = "|{}".format(msg_M1)
    stage3 = "|{}{}".format(msg_M2,msg_memreq)
    state    = " [{}]".format(msg_state)
    pipeline = stage1 + stage2 + stage3 + state
    additional_msg = "data_wben:{}".format(s.data_array_wben_M1)
    # additional_msg = "H1:{}".format(s.hit_M1)

    return pipeline + additional_msg

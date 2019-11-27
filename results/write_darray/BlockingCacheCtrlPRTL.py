"""
=========================================================================
 BlockingCacheCtrlPRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Control
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 15 November 2019
"""

import random

from pymtl3      import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from pymtl3.stdlib.rtl.arithmetics import LShifter
from pymtl3.stdlib.rtl.registers import RegEnRst, RegRst

# Constants
STATE_GO           = b3(0)
STATE_REFILL       = b3(1)
STATE_EVICT        = b3(2)
STATE_REFILL_WRITE = b3(3)
wr = y             = b1(1)
rd = n = x         = b1(0)

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
    tg_wben0 = BitsTagWben(0)
    tg_wbenf = BitsTagWben(-1)
    data_array_wb_mask = 2**(dbw//8)-1
    READ  = BitsType(MemMsgType.READ)
    WRITE = BitsType(MemMsgType.WRITE)
    INIT  = BitsType(MemMsgType.WRITE_INIT)

    #--------------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------------

    s.cachereq_en   = InPort(Bits1)
    s.cachereq_rdy  = OutPort(Bits1)

    s.cacheresp_en  = OutPort(Bits1)
    s.cacheresp_rdy = InPort(Bits1)

    s.memreq_en     = OutPort(Bits1)
    s.memreq_rdy    = InPort(Bits1)

    s.memresp_en    = InPort(Bits1)
    s.memresp_rdy   = OutPort(Bits1)

    #--------------------------------------------------------------------------
    # M0 Ctrl Signals 
    #--------------------------------------------------------------------------

    s.cachereq_type_M0      = InPort (BitsType)
    s.memresp_type_M0       = InPort (BitsType)
    s.MSHR_type             = InPort (BitsType)

    s.memresp_mux_sel_M0    = OutPort(Bits1)
    s.addr_mux_sel_M0       = OutPort(Bits2)
    s.wdata_mux_sel_M0      = OutPort(Bits2)
    s.tag_array_val_M0      = OutPort(Bits1)
    s.tag_array_type_M0     = OutPort(Bits1)
    s.tag_array_wben_M0     = OutPort(BitsTagWben)
    s.ctrl_bit_val_wr_M0    = OutPort(Bits1)
    s.ctrl_bit_dty_wr_M0    = OutPort(Bits1)
    s.reg_en_M0             = OutPort(Bits1)

    #--------------------------------------------------------------------------
    # M1 Ctrl Signals
    #--------------------------------------------------------------------------

    s.cachereq_type_M1      = InPort(BitsType)
    s.ctrl_bit_val_rd_M1    = InPort(Bits1)
    s.ctrl_bit_dty_rd_M1    = InPort(Bits1)
    s.tag_match_M1          = InPort(Bits1)
    s.offset_M1             = InPort(BitsOffset)

    s.reg_en_M1             = OutPort(Bits1)
    s.data_array_val_M1     = OutPort(Bits1)
    s.data_array_type_M1    = OutPort(Bits1)
    s.data_array_wben_M1    = OutPort(BitsDataWben)
    s.reg_en_MSHR           = OutPort(Bits1)
    s.evict_mux_sel_M1      = OutPort(Bits1)

    #---------------------------------------------------------------------------
    # M2 Ctrl Signals
    #--------------------------------------------------------------------------

    s.cachereq_type_M2      = InPort(BitsType)
    s.offset_M2             = InPort(BitsOffset)
    s.reg_en_M2             = OutPort(Bits1)
    s.read_data_mux_sel_M2  = OutPort(mk_bits(clog2(2)))
    s.read_word_mux_sel_M2  = OutPort(BitsRdDataMux)

    # Output Signals
    s.hit_M2                = OutPort(Bits2)
    s.memreq_type           = OutPort(BitsType)

    #--------------------------------------------------------------------------
    # Connection Wires
    #--------------------------------------------------------------------------

    s.is_refill_M0 = Wire(Bits1)
    s.is_refill_M1 = Wire(Bits1)
    s.is_refill_M2 = Wire(Bits1)
    s.hit_M1 = Wire(Bits1)

    #--------------------------------------------------------------------------
    # Stall and Ostall Signals
    #--------------------------------------------------------------------------

    s.stall_M0  = Wire(Bits1)
    s.stall_M1  = Wire(Bits1)
    s.stall_M2  = Wire(Bits1)
    s.ostall_M0 = Wire(Bits1)
    s.ostall_M1 = Wire(Bits1)
    s.ostall_M2 = Wire(Bits1)

    #---------------------------------------------------------------------------
    # Cache-wide FSM
    #--------------------------------------------------------------------------

    # FSM to control refill and evict tranaction conditions. 
    s.curr_state = Wire(Bits3)
    s.next_state = Wire(Bits3)
    s.is_evict_M1 = Wire(Bits1)    

    s.state_transition_block = RegRst(Bits3, STATE_GO)\
    (
      out = s.curr_state,
      in_ = s.next_state
    )

    # FSM STATGE TRANSITION LIVES IN M1 stage but affects behavior in other stage
    # We should not change the FSM stage from any other stage
    @s.update
    def next_state_block():
      s.next_state = STATE_GO
      if s.curr_state == STATE_GO:
        if s.val_M1 and ~s.is_refill_M1 and s.cachereq_type_M1 != INIT:
         if s.is_evict_M1:                     s.next_state = STATE_EVICT 
         elif ~s.hit_M1:                       s.next_state = STATE_REFILL 
      elif s.curr_state == STATE_REFILL:
        if s.is_refill_M0 and s.memresp_type_M0 != WRITE:
          if s.MSHR_type == WRITE:             s.next_state = STATE_REFILL_WRITE
          else:                                s.next_state = STATE_GO
        else:                                  s.next_state = STATE_REFILL
      elif s.curr_state == STATE_EVICT:        s.next_state = STATE_REFILL
      elif s.curr_state == STATE_REFILL_WRITE: s.next_state = STATE_GO

      else:
        assert False, 'undefined state: next state block'

    #--------------------------------------------------------------------------
    # Y Stage 
    #--------------------------------------------------------------------------

    @s.update
    def mem_resp_rdy():
      if s.curr_state == STATE_REFILL: s.memresp_rdy = b1(1)
      else:                            s.memresp_rdy = b1(0)

    #--------------------------------------------------------------------------
    # M0 Stage 
    #---------------------------------------------------------------------------

    s.val_M0 = Wire(Bits1)
    s.is_write_hit_clean_M0 = Wire(Bits1)
    s.is_write_refill_M0 = Wire(Bits1)

    s.is_refill_reg_M0 = RegRst(Bits1)\
    ( # NO STALLS should occur while refilling
      in_ = s.memresp_en,
      out = s.is_refill_M0
    )

    @s.update
    def cachereq_logic():
      s.cachereq_rdy = ~s.stall_M1 and s.curr_state == STATE_GO \
                                   and s.next_state != STATE_REFILL \
                                   and s.next_state != STATE_EVICT \
                                   and s.curr_state != STATE_REFILL_WRITE

      if s.val_M1 and s.cachereq_type_M1 == WRITE and s.is_write_hit_clean_M0:
        s.cachereq_rdy = s.cachereq_rdy and n

    @s.update
    def is_write_refill():
      if s.curr_state == STATE_REFILL_WRITE:
        s.is_write_refill_M0 = y
      else:
        s.is_write_refill_M0 = n

    CS_tag_array_wben_M0  = slice( 9, 9 + twb )
    CS_wdata_mux_sel_M0   = slice( 7, 9 )
    CS_addr_mux_sel_M0    = slice( 5, 7 )
    CS_memresp_mux_sel_M0 = slice( 4, 5 )
    CS_tag_array_type_M0  = slice( 3, 4 )
    CS_tag_array_val_M0   = slice( 2, 3 )
    CS_ctrl_bit_dty_wr_M0 = slice( 1, 2 )
    CS_ctrl_bit_val_wr_M0 = slice( 0, 1 )

    s.cs0 = Wire( mk_bits( 9 + twb ) ) # Bits for control signal table
    @s.update
    def comb_block_M0(): # logic block for setting output ports
      s.val_M0 = s.cachereq_en or (s.is_refill_M0 and s.memresp_type_M0 != WRITE) or s.is_write_refill_M0 or s.is_write_hit_clean_M0
      s.ostall_M0 = b1(0)  # Not sure if neccessary but include for completeness
      s.stall_M0  = s.ostall_M0 or s.ostall_M1 or s.ostall_M2
      s.reg_en_M0 = s.memresp_en and ~s.stall_M0

      #               tag_wben|wdat_mux|addr_mux|memrp_mux|tg_ty|tg_v|dty|val
      s.cs0 = concat( tg_wbenf, b2(0)  , b2(2)  ,    x    ,  rd ,  n , x , x )
      if s.val_M0: #                                          tag_wben|wdat_mux|addr_mux|memrp_mux|tg_ty|tg_v|dty|val
        if s.is_refill_M0:                    s.cs0 = concat( tg_wbenf, b2(1)  , b2(1)  , b1(1)   ,  wr ,  y , n , y )
        elif s.is_write_refill_M0:            s.cs0 = concat( tg_wbenf, b2(2)  , b2(1)  , b1(1)   ,  wr ,  y , y , y )
        elif s.is_write_hit_clean_M0:         s.cs0 = concat( tg_wbenf, b2(0)  , b2(2)  , b1(0)   ,  wr ,  y , y , y )
        else:
          if (s.cachereq_type_M0 == INIT):    s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  , b1(0)   ,  wr ,  y , n , y )
          elif (s.cachereq_type_M0 == READ):  s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  , b1(0)   ,  rd ,  y , n , n )
          elif (s.cachereq_type_M0 == WRITE): s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  , b1(0)   ,  rd ,  y , n , n )
      #     else:                               s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  ,    x    ,  rd ,  n , x , x )
      # else:                                   s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  ,    x    ,  rd ,  n , x , x )      
      s.tag_array_type_M0  = s.cs0[ CS_tag_array_type_M0  ]
      s.tag_array_val_M0   = s.cs0[ CS_tag_array_val_M0   ]
      s.tag_array_wben_M0  = s.cs0[ CS_tag_array_wben_M0  ]
      s.wdata_mux_sel_M0   = s.cs0[ CS_wdata_mux_sel_M0   ]
      s.memresp_mux_sel_M0 = s.cs0[ CS_memresp_mux_sel_M0 ]
      s.addr_mux_sel_M0    = s.cs0[ CS_addr_mux_sel_M0    ]
      s.ctrl_bit_dty_wr_M0 = s.cs0[ CS_ctrl_bit_dty_wr_M0 ]
      s.ctrl_bit_val_wr_M0 = s.cs0[ CS_ctrl_bit_val_wr_M0 ]

    #--------------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------------
    
    s.val_M1 = Wire(Bits1)
    s.is_write_refill_M1 = Wire(Bits1)
    s.is_write_hit_clean_M1 = Wire(Bits1)

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

    s.is_write_hit_clean_reg_M1 = RegRst(Bits1)\
    (
        in_ = s.is_write_hit_clean_M0,
        out = s.is_write_hit_clean_M1
    )

    @s.update
    def hit_logic_M1():
      s.hit_M1 = s.tag_match_M1 and s.ctrl_bit_val_rd_M1 \
                 and s.cachereq_type_M1 != INIT or s.is_write_refill_M1
      if s.is_write_hit_clean_M1:
        s.hit_M1 = s.hit_M1 or b1(1)
      s.hit_M2[1]= b1(0)

    # Calculating shift amount
    # 0 -> 0x000f, 1 -> 0x00f0, 2 -> 0x0f00, 3 -> 0xf000
    s.wben_out = Wire(BitsDataWben)
    s.wben_in  = Wire(BitsDataWben)
    s.WbenGen = LShifter( BitsDataWben, clog2(dwb) )(
      in_ = s.wben_in,
      shamt = s.offset_M1,
      out = s.wben_out
    )

    @s.update
    def en_MSHR(): # TEMPORARY; NOT SURE WHAT TO DO WITH THAT SIGNAL YET
      if not s.hit_M1 and not s.curr_state == STATE_REFILL and ~s.is_evict_M1:
        s.reg_en_MSHR = b1(1)
      else:
        s.reg_en_MSHR = b1(0)

    @s.update
    def is_write_hit_clean_M0_logic():
      if s.cachereq_type_M1 and \
        s.hit_M1 and ~s.ctrl_bit_dty_rd_M1 and \
          ~s.is_write_hit_clean_M1 and ~s.is_write_refill_M1:
        s.is_write_hit_clean_M0 = b1(1)
      else:
        s.is_write_hit_clean_M0 = b1(0)

    @s.update
    def need_evict_M1():
      if s.val_M1 and ~s.is_write_refill_M1 and ~s.hit_M1 and s.ctrl_bit_dty_rd_M1:
        s.is_evict_M1 = b1(1)
      else:
        s.is_evict_M1 = b1(0)

    @s.update
    def en_M1():
      s.reg_en_M1 = ~s.stall_M1 and ~s.is_evict_M1

    CS_data_array_wben_M1   = slice( 4,  4 + dwb )
    CS_data_array_type_M1   = slice( 3,  4 )
    CS_data_array_val_M1    = slice( 2,  3 )
    CS_ostall_M1            = slice( 1,  2 )
    CS_evict_mux_sel_M1     = slice( 0,  1 )

    s.cs1 = Wire( mk_bits( 4 + dwb ) )

    @s.update
    def comb_block_M1():
      s.wben_in = BitsDataWben(data_array_wb_mask)
      wben = s.wben_out
      if s.val_M1: #                                                wben| ty|val|ostall|addr
                   #                                                                    mux  
        if s.is_refill_M1:                          s.cs1 = concat( wben, wr, y , n    , b1(0))
        elif s.is_evict_M1:                         s.cs1 = concat(wben0, rd, y , y    , b1(1))
        elif s.is_write_hit_clean_M1:               s.cs1 = concat(wbenf, x , n , n    , b1(0))
        else:
          if s.cachereq_type_M1 == INIT:            s.cs1 = concat( wben, wr, y , n    , b1(0))
          elif ~s.hit_M1 and ~s.ctrl_bit_dty_rd_M1: s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif ~s.hit_M1 and  s.ctrl_bit_dty_rd_M1: s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif  s.hit_M1 and ~s.ctrl_bit_dty_rd_M1:
            if   s.cachereq_type_M1 == READ:        s.cs1 = concat(wben0, rd, y , n    , b1(0))
            elif s.cachereq_type_M1 == WRITE:       s.cs1 = concat( wben, wr, y , n    , b1(0))
            else:                                   s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif  s.hit_M1 and  s.ctrl_bit_dty_rd_M1:
            if   s.cachereq_type_M1 == READ:        s.cs1 = concat(wben0, rd, y , n    , b1(0))
            elif s.cachereq_type_M1 == WRITE:       s.cs1 = concat( wben, wr, y , n    , b1(0))
      else:                                         s.cs1 = concat(wben0, x , n , n    , b1(0))

      s.data_array_type_M1        = s.cs1[ CS_data_array_type_M1 ]
      s.data_array_val_M1         = s.cs1[ CS_data_array_val_M1  ]
      s.data_array_wben_M1        = s.cs1[ CS_data_array_wben_M1 ]
      s.ostall_M1                 = s.cs1[ CS_ostall_M1          ]
      s.evict_mux_sel_M1          = s.cs1[ CS_evict_mux_sel_M1   ]
      s.stall_M1 = s.ostall_M1 or s.ostall_M2

    #--------------------------------------------------------------------------
    # M2 Stage
    #--------------------------------------------------------------------------

    s.val_M2                = Wire(Bits1)
    s.is_evict_M2           = Wire(Bits1)
    s.is_write_refill_M2    = Wire(Bits1)
    s.is_write_hit_clean_M2 = Wire(Bits1)

    s.val_reg_M2 = RegEnRst(Bits1)\
    (
      en  = s.reg_en_M2,
      in_ = s.val_M1,
      out = s.val_M2,
    )

    s.is_evict_reg_M2 = RegEnRst(Bits1)\
    (
      en  = s.reg_en_M2,
      in_ = s.is_evict_M1,
      out = s.is_evict_M2
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

    s.is_write_hit_clean_reg_M2 = RegRst(Bits1)\
    (
        in_ = s.is_write_hit_clean_M1,
        out = s.is_write_hit_clean_M2
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
      s.msel = BitsRdDataMux(s.offset_M2[2:ofw]) + BitsRdDataMux(1)  
      if s.val_M2:                                     #  word_mux|rdata_mux|ostall|memreq_type|memreq|cacheresp
        if ~s.memreq_rdy or ~s.cacheresp_rdy:s.cs2 = concat(mxsel0,   b1(0) ,  y   ,   READ    ,    n ,     n   )
        elif s.is_evict_M2:                  s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   WRITE   ,    y ,     n   )
        elif s.is_refill_M2:
          if s.cachereq_type_M2 == READ:     s.cs2 = concat(s.msel,   b1(1) ,  n   ,   READ    ,    n ,     y   )
          elif s.cachereq_type_M2 == WRITE:  s.cs2 = concat(mxsel0,   b1(1) ,  n   ,   READ    ,    n ,     y   )
        elif s.is_write_hit_clean_M2:        s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     n   )
        else:
          if s.cachereq_type_M2 == INIT:     s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     y   )
          elif s.cachereq_type_M2 == READ:
            if    s.hit_M2[0]:               s.cs2 = concat(s.msel,   b1(0) ,  n   ,   READ    ,    n ,     y   )
            elif ~s.hit_M2[0]:               s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    y ,     n   )
          elif s.cachereq_type_M2 == WRITE:
            if s.is_write_refill_M2:         s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     n   )
            elif  s.hit_M2[0]:               s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     y   )
            elif ~s.hit_M2[0]:               s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    y ,     n   )
      else:                                  s.cs2 = concat(mxsel0,   b1(0) ,  n   ,   READ    ,    n ,     n   )

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
    msg_M0 = "  "
    if s.val_M0:
      if s.is_refill_M0 and s.cachereq_rdy:
        msg_M0 = "rf"
      elif s.is_refill_M0 and not s.cachereq_rdy:
        msg_M0 = "#r"
      elif s.is_write_hit_clean_M0 and s.cachereq_rdy:
        msg_M0 = "wc"
      elif s.is_write_hit_clean_M0 and not s.cachereq_rdy:
        msg_M0 = "#w"
      else:
        if s.is_write_refill_M0:
          msg_M0 = "wf"
        elif s.val_M0:
          msg_M0 = types[s.cachereq_type_M0]
    elif not s.cachereq_rdy:
      msg_M0 = "# "

    msg_M1 = "  "
    if s.val_M1:
      if s.is_refill_M1:
        msg_M1 = "rf"
      elif s.is_write_hit_clean_M1:
        msg_M1 = "wc"
      elif ~s.hit_M1 and s.cachereq_type_M1 != 2:
        msg_M1 = colors['RED'] + types[s.cachereq_type_M1] + colors['WHITE']
      elif s.is_write_refill_M1:
        msg_M1 = "wf"
      elif s.hit_M1 and s.cachereq_type_M1 != 2:
        msg_M1 = colors['GREEN'] + types[s.cachereq_type_M1] + colors['WHITE']
      else:
        msg_M1 = types[s.cachereq_type_M1]

    msg_M2 = "  "
    if s.val_M2:
      if s.is_refill_M2:            msg_M2 = "rf"
      elif s.is_write_hit_clean_M2: msg_M2 = "wc"
      elif s.is_write_refill_M2:    msg_M2 = "wf"
      elif s.is_evict_M2:           msg_M2 = "ev"
      else:                         msg_M2 = types[s.cachereq_type_M2]

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

    return pipeline
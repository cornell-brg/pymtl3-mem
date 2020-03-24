"""
=========================================================================
 BlockingCacheCtrlRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Control
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from .ReplacementPolicy            import ReplacementPolicy
from colorama                      import Fore, Back, Style
from mem_pclib.constants.constants import *
from pymtl3                        import *
from pymtl3.stdlib.rtl.arithmetics import LeftLogicalShifter
from pymtl3.stdlib.rtl.registers   import RegEnRst, RegRst
from mem_pclib.rtl.registers       import CtrlPipelineReg

#=========================================================================
# Constants
#=========================================================================

# M0 FSM states
M0_FSM_STATE_NBITS = 1

M0_FSM_STATE_READY  = b1(0) # ready to take new request
M0_FSM_STATE_REPLAY = b1(1) # replay the previous miss request

# Ctrl pipeline states
CTRL_STATE_NBITS = 3

CTRL_STATE_INVALID      = b3(0)
CTRL_STATE_REFILL_READ  = b3(1)
CTRL_STATE_REFILL_WRITE = b3(2)
CTRL_STATE_CLEAN_HIT    = b3(3)
CTRL_STATE_READ_REQ     = b3(4)
CTRL_STATE_WRITE_REQ    = b3(5)
CTRL_STATE_INIT_REQ     = b3(6)

#=========================================================================
# BlockingCacheCtrlRTL
#=========================================================================

class BlockingCacheCtrlRTL ( Component ):

  def construct( s, p ):

    # Constants (required for translation to work)
    associativity = p.associativity

    #--------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------

    s.cachereq_en   = InPort ( Bits1 )
    s.cachereq_rdy  = OutPort( Bits1 )

    s.cacheresp_en  = OutPort( Bits1 )
    s.cacheresp_rdy = InPort ( Bits1 )

    s.memreq_en     = OutPort( Bits1 )
    s.memreq_rdy    = InPort ( Bits1 )

    s.memresp_en    = InPort ( Bits1 )
    s.memresp_rdy   = OutPort( Bits1 )

    s.status        = InPort ( p.StructStatus )
    s.ctrl          = OutPort( p.StructCtrl )

    #--------------------------------------------------------------------
    # Y Stage
    #--------------------------------------------------------------------

    @s.update
    def mem_resp_rdy():
      s.memresp_rdy = y # Always yes

    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------

    s.memresp_en_M0 = RegEnRst( Bits1 )(
      in_ = s.memresp_en,
      en  = s.ctrl.reg_en_M0
    )

    # Checks if memory response if valid
    s.memresp_val_M0 = Wire( Bits1 )
    s.memresp_val_M0 //= lambda: s.memresp_en_M0.out & ( s.status.memresp_type_M0 != WRITE )

    s.FSM_state_M0_next = Wire( mk_bits(M0_FSM_STATE_NBITS) )
    s.FSM_state_M0 = RegEnRst( mk_bits(M0_FSM_STATE_NBITS), reset_value=M0_FSM_STATE_READY )(
      in_ = s.FSM_state_M0_next,
      en  = s.ctrl.reg_en_M0
    )

    @s.update
    def fsm_M0_next_state():
      s.FSM_state_M0_next = M0_FSM_STATE_READY
      if s.FSM_state_M0.out == M0_FSM_STATE_READY:
        if s.memresp_val_M0 and (~s.status.MSHR_empty):
          # Have valid replays in the MSHR
          s.FSM_state_M0_next = M0_FSM_STATE_REPLAY
      elif s.FSM_state_M0.out == M0_FSM_STATE_REPLAY:
        if not s.status.MSHR_empty:
          # stay in this state if MSHR is not cleared
          s.FSM_state_M0_next = M0_FSM_STATE_REPLAY

    # If we hitting a clean word, we need to update the dirty bits, set in M1 stage.
    s.is_write_hit_clean_M0 = Wire( Bits1 )

    # M0 States

    s.state_M0 = Wire( mk_bits(CTRL_STATE_NBITS) )

    @s.update
    def state_logic_M0():
      s.state_M0 = CTRL_STATE_INVALID

      if   s.is_write_hit_clean_M0:
        s.state_M0 = CTRL_STATE_CLEAN_HIT
      elif s.FSM_state_M0.out == M0_FSM_STATE_REPLAY:
        if not s.status.MSHR_empty:
          if s.status.MSHR_type == WRITE:
            s.state_M0 = CTRL_STATE_REFILL_WRITE
          elif s.status.MSHR_type == READ:
            s.state_M0 = CTRL_STATE_REFILL_READ
      elif s.FSM_state_M0.out == M0_FSM_STATE_READY:
        if s.memresp_val_M0:
          s.state_M0 = CTRL_STATE_REFILL_READ

      if s.status.MSHR_empty and s.cachereq_en:
        if s.status.cachereq_type_M0 == INIT:
          s.state_M0 = CTRL_STATE_INIT_REQ
        elif s.status.cachereq_type_M0 == READ:
          s.state_M0 = CTRL_STATE_READ_REQ
        elif s.status.cachereq_type_M0 == WRITE:
          s.state_M0 = CTRL_STATE_WRITE_REQ

    @s.update
    def MSHR_dealloc_en_logic_M0():
      s.ctrl.MSHR_dealloc_en = n
      if s.FSM_state_M0.out == M0_FSM_STATE_READY:
        if s.memresp_val_M0:
          if s.status.MSHR_type == READ: # If read, then we dealloc and run
            s.ctrl.MSHR_dealloc_en = y   # the read cachereq with the refill

      elif s.FSM_state_M0.out == M0_FSM_STATE_REPLAY:
        if not s.status.MSHR_empty:
          s.ctrl.MSHR_dealloc_en = y

    s.stall_M0 = Wire( Bits1 )

    # Stalls originating from M1 and M2
    s.ostall_M1 = Wire( Bits1 )
    s.ostall_M2 = Wire( Bits1 )

    s.stall_M0 //= lambda: s.ostall_M1 | s.ostall_M2

    @s.update
    def cachereq_rdy_logic():
      s.cachereq_rdy = y
      if s.is_write_hit_clean_M0:
        s.cachereq_rdy = n
      elif s.stall_M0: # stall in the cache due to evict, stalls in M1 and M2
        s.cachereq_rdy = n
      elif s.status.MSHR_full or not s.status.MSHR_empty:
        # no space in MSHR or we have replay
        s.cachereq_rdy = n

    # M0 control signal table
    s.cs0 = Wire( mk_bits( 5 + p.bitwidth_tag_wben ) )

    CS_tag_array_wben_M0  = slice( 5, 5 + p.bitwidth_tag_wben )
    CS_wdata_mux_sel_M0   = slice( 4, 5 )
    CS_addr_mux_sel_M0    = slice( 3, 4 )
    CS_memresp_mux_sel_M0 = slice( 2, 3 )
    CS_tag_array_type_M0  = slice( 1, 2 )
    CS_ctrl_bit_val_wr_M0 = slice( 0, 1 )

    tg_wbenf = p.tg_wbenf

    @s.update
    def cs_table_M0():
      #                                                            tag_wben|wdat_mux|addr_mux|memrp_mux|tg_ty|val
      s.cs0 =                                             concat( tg_wbenf, b1(0),   b1(0),      x ,    rd,   x )
      if   s.state_M0 == CTRL_STATE_REFILL_READ:  s.cs0 = concat( tg_wbenf, b1(1),   b1(0),   b1(1),    wr,   y )
      elif s.state_M0 == CTRL_STATE_REFILL_WRITE: s.cs0 = concat( tg_wbenf, b1(0),   b1(0),   b1(1),    wr,   y )
      elif s.state_M0 == CTRL_STATE_CLEAN_HIT:    s.cs0 = concat( tg_wbenf, b1(0),   b1(1),   b1(0),    wr,   y )
      elif s.state_M0 == CTRL_STATE_INIT_REQ:     s.cs0 = concat( tg_wbenf, b1(0),   b1(0),   b1(0),    wr,   y )
      elif s.state_M0 == CTRL_STATE_READ_REQ:     s.cs0 = concat( tg_wbenf, b1(0),   b1(0),   b1(0),    rd,   n )
      elif s.state_M0 == CTRL_STATE_WRITE_REQ:    s.cs0 = concat( tg_wbenf, b1(0),   b1(0),   b1(0),    rd,   n )

      s.ctrl.tag_array_wben_M0  = s.cs0[ CS_tag_array_wben_M0  ]
      s.ctrl.wdata_mux_sel_M0   = s.cs0[ CS_wdata_mux_sel_M0   ]
      s.ctrl.addr_mux_sel_M0    = s.cs0[ CS_addr_mux_sel_M0    ]
      s.ctrl.memresp_mux_sel_M0 = s.cs0[ CS_memresp_mux_sel_M0 ]
      s.ctrl.tag_array_type_M0  = s.cs0[ CS_tag_array_type_M0  ]
      s.ctrl.ctrl_bit_val_wr_M0 = s.cs0[ CS_ctrl_bit_val_wr_M0 ]
      # s.ctrl.ctrl_bit_dty_wr_M0 = s.cs0[ CS_ctrl_bit_dty_wr_M0 ]

      # Control signals output
      s.ctrl.is_write_refill_M0 = (s.state_M0 == CTRL_STATE_REFILL_WRITE)
      s.ctrl.is_write_hit_clean_M0 = s.is_write_hit_clean_M0
      s.ctrl.reg_en_M0 = ~s.stall_M0
      s.ctrl.ctrl_bit_dty_wr_M0 = s.status.new_dirty_bits_M0

    @s.update
    def tag_array_val_logic_M0():
      # Most of the logic is for associativity > 1; should simplify for dmapped
      for i in range( associativity ):
        s.ctrl.tag_array_val_M0[i] = n # Enable all SRAMs since we are reading
      if s.state_M0 == CTRL_STATE_REFILL_READ:
        s.ctrl.tag_array_val_M0[s.status.MSHR_ptr] = y
      elif s.state_M0 == CTRL_STATE_REFILL_WRITE:
        s.ctrl.tag_array_val_M0[s.status.MSHR_ptr] = y
      elif s.state_M0 == CTRL_STATE_INIT_REQ:
        s.ctrl.tag_array_val_M0[s.status.ctrl_bit_rep_rd_M1] = y
      elif s.state_M0 == CTRL_STATE_CLEAN_HIT:
        s.ctrl.tag_array_val_M0[s.status.hit_way_M1] = y
      elif s.state_M0 == CTRL_STATE_READ_REQ or s.state_M0 == CTRL_STATE_WRITE_REQ:
        for i in range( associativity ):
          s.ctrl.tag_array_val_M0[i] = y # Enable all SRAMs since we are reading

    #--------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------

    s.state_M1 = RegEnRst( mk_bits(CTRL_STATE_NBITS) )(
      in_ = s.state_M0,
      en  = s.ctrl.reg_en_M1,
    )

    # Indicates which way in the cache to replace. We receive the value from
    # dealloc in the M0 stage and use it in both M0 and M1
    s.way_ptr_M1 = RegEnRst( p.BitsAssoclog2 )(
      in_ = s.status.MSHR_ptr,
      en  = s.ctrl.reg_en_M1,
    )

    s.hit_M1            = Wire( Bits1 )
    s.is_evict_M1       = Wire( Bits1 )
    s.stall_M1          = Wire( Bits1 )
    s.is_dty_M1         = Wire( Bits1 )
    s.is_line_valid_M1  = Wire( Bits1 )
    # EXTRA Logic for accounting for set associative caches
    s.repreq_en_M1      = Wire( Bits1 )
    s.repreq_is_hit_M1  = Wire( Bits1 )
    s.repreq_hit_ptr_M1 = Wire( p.BitsAssoclog2 )

    s.stall_M1 //= lambda: s.ostall_M1 | s.ostall_M2

    # TODO: Need more work
    s.replacement_M1 = ReplacementPolicy(
      p.BitsAssoc, p.BitsAssoclog2, associativity, 0
    )(
      repreq_en       = s.repreq_en_M1,
      repreq_hit_ptr  = s.repreq_hit_ptr_M1,
      repreq_is_hit   = s.repreq_is_hit_M1,
      repreq_ptr      = s.status.ctrl_bit_rep_rd_M1, # Read replacement mask
      represp_ptr     = s.ctrl.ctrl_bit_rep_wr_M0,   # Bypass to M0 stage?
    )

    # Selects the index offset for the Data array based on which way to
    # read/write. We only use one data array and we have offset the index
    @s.update
    def asso_data_array_offset_way_M1():
      s.ctrl.way_offset_M1 = s.status.hit_way_M1
      if s.state_M1.out == CTRL_STATE_REFILL_READ or s.state_M1.out == CTRL_STATE_REFILL_WRITE:
        s.ctrl.way_offset_M1 = s.way_ptr_M1.out
      elif s.state_M1.out == CTRL_STATE_READ_REQ or s.state_M1.out == CTRL_STATE_WRITE_REQ:
        if s.is_evict_M1:
          s.ctrl.way_offset_M1 = s.status.ctrl_bit_rep_rd_M1

    # Change M0 state in case of writing to a clean bits
    @s.update
    def write_hit_clean_logic_M1():
      s.is_write_hit_clean_M0 = n
      if s.is_line_valid_M1 and (s.state_M1.out == CTRL_STATE_WRITE_REQ):
        if s.hit_M1 and not s.status.ctrl_bit_dty_rd_M1[s.status.hit_way_M1]:
          s.is_write_hit_clean_M0 = y

    # Determines the status of the M1 stage
    @s.update
    def status_logic_M1():
      s.is_evict_M1       = n
      s.is_dty_M1         = s.status.ctrl_bit_dty_rd_M1[s.status.ctrl_bit_rep_rd_M1]
      # Bits for set associative caches
      s.repreq_is_hit_M1  = n
      s.repreq_en_M1      = n
      s.repreq_hit_ptr_M1 = x
      s.hit_M1            = n
      s.is_line_valid_M1  = s.status.line_valid_M1[s.status.ctrl_bit_rep_rd_M1]

      if s.state_M1.out != CTRL_STATE_INVALID:
        if s.state_M1.out != CTRL_STATE_REFILL_READ and s.state_M1.out != CTRL_STATE_REFILL_WRITE:
          s.hit_M1 = s.status.hit_M1
          # if hit, dty bit will come from the way where the hit occured
          if s.hit_M1:
            s.is_dty_M1 = s.status.ctrl_bit_dty_rd_M1[s.status.hit_way_M1]
            s.is_line_valid_M1 = s.status.line_valid_M1[s.status.hit_way_M1]

          if s.state_M1.out == CTRL_STATE_INIT_REQ:
            s.repreq_en_M1      = y
            s.repreq_is_hit_M1  = n

          if not s.hit_M1 and s.is_dty_M1 and s.is_line_valid_M1:
            s.is_evict_M1 = y

          if not s.is_evict_M1 and s.state_M1.out != CTRL_STATE_CLEAN_HIT:
            # Better to update replacement bit right away because we need it
            # for nonblocking capability. For blocking, we can also update
            # during a refill for misses
            s.repreq_en_M1      = y
            s.repreq_hit_ptr_M1 = s.status.hit_way_M1
            s.repreq_is_hit_M1  = s.hit_M1

      s.ctrl.ctrl_bit_rep_en_M1 = s.repreq_en_M1 & ~s.stall_M1

    # Calculating shift amount
    # 0 -> 0x000f, 1 -> 0x00f0, 2 -> 0x0f00, 3 -> 0xf000
    s.wben_in    = Wire(p.BitsDataWben)
    BitsDataWben = p.BitsDataWben
    BitsLen      = p.BitsLen

    @s.update
    def mask_select_M1():
      if s.status.len_M1 == BitsLen(0):
        s.wben_in = BitsDataWben( data_array_word_mask )
      elif s.status.len_M1 == BitsLen(1):
        s.wben_in = BitsDataWben( data_array_byte_mask )
      elif s.status.len_M1 == BitsLen(2):
        s.wben_in = BitsDataWben( data_array_2byte_mask )
      else:
        s.wben_in = BitsDataWben( data_array_word_mask )
    s.WbenGen = LeftLogicalShifter( BitsDataWben, clog2(p.bitwidth_data_wben) )(
      in_ = s.wben_in,
      shamt = s.status.offset_M1,
    )

    # M1 control signal table
    s.cs1 = Wire( mk_bits( 5 + p.bitwidth_data_wben ) )

    CS_data_array_wben_M1 = slice( 5, 5 + p.bitwidth_data_wben )
    CS_data_array_type_M1 = slice( 4, 5 )
    CS_data_array_val_M1  = slice( 3, 4 )
    CS_ostall_M1          = slice( 2, 3 )
    CS_evict_mux_sel_M1   = slice( 1, 2 )
    CS_MSHR_alloc_en      = slice( 0, 1 )

    wben0 = p.BitsDataWben( 0 )
    wbenf = p.BitsDataWben( -1 )

    @s.update
    def signal_select_logic_M1():
      wben = s.WbenGen.out

      #                                                               wben| ty|val|ostall|evict mux|alloc_en
      s.cs1                                                 = concat(wben0, x , n , n    , b1(0)   ,   n   )
      if   s.state_M1.out == CTRL_STATE_INVALID:      s.cs1 = concat(wben0, x , n , n    , b1(0)   ,   n   )
      elif s.state_M1.out == CTRL_STATE_REFILL_READ:  s.cs1 = concat(wbenf, wr, y , n    , b1(0)   ,   n   )
      elif s.state_M1.out == CTRL_STATE_REFILL_WRITE: s.cs1 = concat( wben, wr, y , n    , b1(0)   ,   n   )
      elif s.state_M1.out == CTRL_STATE_CLEAN_HIT:    s.cs1 = concat(wbenf, x , n , n    , b1(0)   ,   n   )
      elif s.is_evict_M1:                             s.cs1 = concat(wben0, rd, y , y    , b1(1)   ,   y   )
      elif s.state_M1.out == CTRL_STATE_INIT_REQ:     s.cs1 = concat( wben, wr, y , n    , b1(0)   ,   n   )
      elif ~s.hit_M1 and ~s.is_dty_M1:                s.cs1 = concat(wben0, x , n , n    , b1(0)   ,   y   )
      elif ~s.hit_M1 and  s.is_dty_M1:                s.cs1 = concat(wben0, x , n , n    , b1(0)   ,   y   )
      elif  s.hit_M1 and ~s.is_dty_M1:
        if   s.state_M1.out == CTRL_STATE_READ_REQ:   s.cs1 = concat(wben0, rd, y , n    , b1(0)   ,   n   )
        elif s.state_M1.out == CTRL_STATE_WRITE_REQ:  s.cs1 = concat( wben, wr, y , n    , b1(0)   ,   n   )
      elif  s.hit_M1 and  s.is_dty_M1:
        if   s.state_M1.out == CTRL_STATE_READ_REQ:   s.cs1 = concat(wben0, rd, y , n    , b1(0)   ,   n   )
        elif s.state_M1.out == CTRL_STATE_WRITE_REQ:  s.cs1 = concat( wben, wr, y , n    , b1(0)   ,   n   )

      s.ctrl.data_array_wben_M1 = s.cs1[ CS_data_array_wben_M1 ]
      s.ctrl.data_array_type_M1 = s.cs1[ CS_data_array_type_M1 ]
      s.ctrl.data_array_val_M1  = s.cs1[ CS_data_array_val_M1  ]
      s.ostall_M1               = s.cs1[ CS_ostall_M1          ]
      s.ctrl.evict_mux_sel_M1   = s.cs1[ CS_evict_mux_sel_M1   ]
      s.ctrl.MSHR_alloc_en      = s.cs1[ CS_MSHR_alloc_en      ] & ~s.stall_M1
      s.ctrl.reg_en_M1 = ~s.stall_M1 & ~s.is_evict_M1

    s.was_stalled = RegRst( Bits1 )(
      in_ = s.ostall_M2,
    )

    @s.update
    def stall_logic_M1():
      # Logic for the SRAM tag array as a result of a stall in cache since the
      # values from the SRAM are valid for one cycle
      s.ctrl.stall_mux_sel_M1 = s.was_stalled.out
      s.ctrl.stall_reg_en_M1  = ~s.was_stalled.out

    #--------------------------------------------------------------------
    # M2 Stage
    #--------------------------------------------------------------------

    s.state_M2 = RegEnRst( mk_bits(CTRL_STATE_NBITS) )(
      en  = s.ctrl.reg_en_M2,
      in_ = s.state_M1.out,
    )

    s.is_evict_M2 = RegEnRst( Bits1 )(
      in_ = s.is_evict_M1,
      en  = s.ctrl.reg_en_M2,
    )

    s.hit_reg_M2 = RegEnRst( Bits1 )(
      in_ = s.hit_M1,
      en  = s.ctrl.reg_en_M2,
      out = s.ctrl.hit_M2[0],
    )

    s.stall_M2  = Wire( Bits1 )
    s.stall_M2 //= s.ostall_M2

    # M2 control signal table

    s.cs2 = Wire( Bits9 )

    CS_data_size_mux_en_M2  = slice( 8,  9 )
    CS_read_data_mux_sel_M2 = slice( 7,  8 )
    CS_ostall_M2            = slice( 6,  7 )
    CS_memreq_type          = slice( 2,  6 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )

    @s.update
    def comb_block_M2():
      s.ctrl.hit_M2[1] = b1(0) # hit output expects 2 bits but we only use one bit

      #                                                               dsize_en|rdata_mux|ostall|memreq_type|memreq|cacheresp
      s.cs2                                                 = concat( y,       b1(0),    n,     READ,       n,     n        )
      if   s.state_M2.out == CTRL_STATE_INVALID:      s.cs2 = concat( y,       b1(0),    n,     READ,       n,     n        )
      elif s.state_M2.out == CTRL_STATE_CLEAN_HIT:    s.cs2 = concat( y,       b1(0),    n,     READ,       n,     n        )
      elif ~s.memreq_rdy or ~s.cacheresp_rdy:         s.cs2 = concat( n,       b1(0),    y,     READ,       n,     n        )
      elif s.is_evict_M2.out:                         s.cs2 = concat( n,       b1(0),    n,     WRITE,      y,     n        )
      elif s.state_M2.out == CTRL_STATE_REFILL_READ:
        if s.status.cachereq_type_M2 == READ:         s.cs2 = concat(   y   ,  b1(1) ,  n    ,   READ    ,    n ,     y   )
        # elif s.status.cachereq_type_M2 == WRITE:      s.cs2 = concat(   n   ,  b1(1) ,  n    ,   READ    ,    n ,     n   )
      else:
        if s.status.cachereq_type_M2 == INIT:    s.cs2 = concat(   n   ,  b1(0) ,  n    ,   READ    ,    n ,     y   )
        elif s.status.cachereq_type_M2 == READ:
          if    s.ctrl.hit_M2[0]:                s.cs2 = concat(   y   ,  b1(0) ,  n    ,   READ    ,    n ,     y   )
          elif ~s.ctrl.hit_M2[0]:                s.cs2 = concat(   n   ,  b1(0) ,  n    ,   READ    ,    y ,     n   )
        elif s.status.cachereq_type_M2 == WRITE:
          if s.state_M2.out == CTRL_STATE_REFILL_WRITE:     s.cs2 = concat(   n   ,  b1(0) ,  n    ,   WRITE   ,    n ,     y   )
          elif  s.ctrl.hit_M2[0]:                s.cs2 = concat(   n   ,  b1(0) ,  n    ,   READ    ,    n ,     y   )
          elif ~s.ctrl.hit_M2[0]:                s.cs2 = concat(   n   ,  b1(0) ,  n    ,   READ    ,    y ,     n   )

      s.ctrl.data_size_mux_en_M2  = s.cs2[ CS_data_size_mux_en_M2  ]
      s.ctrl.read_data_mux_sel_M2 = s.cs2[ CS_read_data_mux_sel_M2 ]
      s.ostall_M2                 = s.cs2[ CS_ostall_M2            ]
      s.ctrl.memreq_type          = s.cs2[ CS_memreq_type          ]
      s.cacheresp_en              = s.cs2[ CS_cacheresp_en         ]
      s.memreq_en                 = s.cs2[ CS_memreq_en            ]

      s.ctrl.reg_en_M2 = ~s.stall_M2

    @s.update
    def stall_logic_M2():
      s.ctrl.stall_mux_sel_M2 = s.was_stalled.out
      s.ctrl.stall_reg_en_M2 = ~s.was_stalled.out

  #-----------------------------------------------------------------------
  # line_trace
  #-----------------------------------------------------------------------

  def line_trace( s ):
    msg_M0 = "  "
    if s.state_M0 == CTRL_STATE_INVALID:
      if not s.cachereq_rdy:
        msg_M0 = "# "
    elif s.state_M0 == CTRL_STATE_REFILL_READ:
      if s.cachereq_rdy:
        msg_M0 = "rf"
      else:
        msg_M0 = "#r"
    elif s.state_M0 == CTRL_STATE_CLEAN_HIT:
      if s.cachereq_rdy:
        msg_M0 = "wc"
      else:
        msg_M0 = "#w"
    elif s.state_M0 == CTRL_STATE_REFILL_WRITE:
      msg_M0 = "wf"
    elif s.state_M0 == CTRL_STATE_READ_REQ:
      msg_M0 = "rd"
    elif s.state_M0 == CTRL_STATE_WRITE_REQ:
      msg_M0 = "wr"
    elif s.state_M0 == CTRL_STATE_INIT_REQ:
      msg_M0 = "in"

    msg_M1 = "  "
    color_m1 = Back.BLACK + Fore.GREEN if s.hit_M1 else Back.BLACK + Fore.RED

    if s.state_M1.out == CTRL_STATE_REFILL_READ:
      msg_M1 = "rf"
    elif s.state_M1.out == CTRL_STATE_CLEAN_HIT:
      msg_M1 = "wc"
    elif s.state_M1.out == CTRL_STATE_REFILL_WRITE:
      msg_M1 = "wf"
    elif s.state_M1.out == CTRL_STATE_READ_REQ:
      msg_M1 = color_m1 + "rd" + Style.RESET_ALL
    elif s.state_M1.out == CTRL_STATE_WRITE_REQ:
      msg_M1 = color_m1 + "wr" + Style.RESET_ALL
    elif s.state_M1.out == CTRL_STATE_INIT_REQ:
      msg_M0 = "in"

    msg_M2 = "  "
    if   s.state_M2.out == CTRL_STATE_REFILL_READ:  msg_M2 = "rf"
    elif s.state_M2.out == CTRL_STATE_CLEAN_HIT:    msg_M2 = "wc"
    elif s.state_M2.out == CTRL_STATE_REFILL_WRITE: msg_M2 = "wf"
    elif s.is_evict_M2.out:                         msg_M2 = "ev"
    elif s.state_M2.out == CTRL_STATE_READ_REQ:     msg_M2 = "rd"
    elif s.state_M2.out == CTRL_STATE_WRITE_REQ:    msg_M2 = "wr"
    elif s.state_M2.out == CTRL_STATE_INIT_REQ:     msg_M2 = "in"

    msg_memresp = ">" if s.memresp_en else " "
    msg_memreq = ">" if s.memreq_en else " "

    stage1 = "{}|{}".format(msg_memresp,msg_M0) if s.memresp_en \
      else "  {}".format(msg_M0)
    stage2 = "|{}".format(msg_M1)
    stage3 = "|{}{}".format(msg_M2,msg_memreq)
    pipeline = stage1 + stage2 + stage3
    add_msgs = ""
    # add_msgs = f"dty:{s.status.ctrl_bit_dty_rd_M1}"
    return pipeline + add_msgs

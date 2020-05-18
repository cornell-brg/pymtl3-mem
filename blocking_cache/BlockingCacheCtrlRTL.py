"""
=========================================================================
 BlockingCacheCtrlRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Control
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from colorama                      import Fore, Back, Style

from pymtl3                        import *
from pymtl3.stdlib.rtl.registers   import RegEnRst, RegRst
from constants.constants import *
from .ReplacementPolicy            import ReplacementPolicy
from .constants                    import *
from .units.counters               import CounterEnRst

#=========================================================================
# Constants
#=========================================================================

#-------------------------------------------------------------------------
# M0 FSM states
#-------------------------------------------------------------------------

M0_FSM_STATE_NBITS = 3

M0_FSM_STATE_INIT       = b3(0) # tag array initialization
M0_FSM_STATE_READY      = b3(1) # ready to serve the request from proc or MSHR
M0_FSM_STATE_REPLAY     = b3(2) # replay the previous request from MSHR
M0_FSM_STATE_INV        = b3(3) # INV
M0_FSM_STATE_FLUSH      = b3(4) # Flush
M0_FSM_STATE_FLUSH_WAIT = b3(5) # Flush, waiting for response

#-------------------------------------------------------------------------
# Control Transactions
#-------------------------------------------------------------------------
# Typical transaction sequences:
# Cache initialization: TRANS_TYPE_CACHE_INIT
# Read hit:   TRANS_TYPE_READ_REQ
# Write hit:  TRANS_TYPE_WRITE_REQ -> TRANS_TYPE_CLEAN_HIT
# Read miss:  TRANS_TYPE_READ_REQ  -> TRANS_TYPE_REPLAY_READ
# Write miss: TRANS_TYPE_READ_REQ  -> TRANS_TYPE_REFILL ->
#             TRANS_TYPE_REPLAY_WRITE
# init-write: TRANS_TYPE_INIT_REQ
# Cache inv:  TRANS_TYPE_INV_START ->
#             (TRANS_TYPE_INV_WRITE) x (N-1 times) ->
#             TRANS_TYPE_REPLAY_INV
# Cache flush: TRANS_TYPE_FLUSH_START ->
#              (TRANS_TYPE_FLUSH_READ -> TRANS_TYPE_FLUSH_WAIT -> TRANS_TYPE_FLUSH_WRITE) x N ->
#              TRANS_TYPE_REPLAY_INV
#

TRANS_TYPE_NBITS = 5

TRANS_TYPE_INVALID      = b5(0)

# Normal read/write
TRANS_TYPE_REFILL       = b5(1)  # Refill only (for write-miss)
TRANS_TYPE_REPLAY_READ  = b5(2)  # Replay the read miss along with refill
TRANS_TYPE_REPLAY_WRITE = b5(3)  # Replay the write miss after refill
TRANS_TYPE_CLEAN_HIT    = b5(4)  # M1 stage hit a clean word, update dirty bits
TRANS_TYPE_READ_REQ     = b5(5)  # Read req from cachereq
TRANS_TYPE_WRITE_REQ    = b5(6)  # Write req from cachereq
TRANS_TYPE_INIT_REQ     = b5(7)  # Init-write req from cachereq

# Cache initialization
TRANS_TYPE_CACHE_INIT   = b5(8)  # Init cache

# Atomics
TRANS_TYPE_AMO_REQ      = b5(9)  # AMO req from cachereq
TRANS_TYPE_REPLAY_AMO   = b5(10) # Replay the AMO req after receiving memresp

# Cache invalidation
TRANS_TYPE_INV_START    = b5(11) # Start the inv req
TRANS_TYPE_INV_WRITE    = b5(12) # Inv req: write tag arrays
TRANS_TYPE_REPLAY_INV   = b5(13) # Replay the INV req after is done

# Cache flush
TRANS_TYPE_FLUSH_START  = b5(14) # Start the flush req
TRANS_TYPE_FLUSH_READ   = b5(15) # flush req: read tag arrays
TRANS_TYPE_FLUSH_WAIT   = b5(16) # flush req: wait for memresp write ack
TRANS_TYPE_FLUSH_WRITE  = b5(17) # flush req: write tag arrays
TRANS_TYPE_REPLAY_FLUSH = b5(18) # Replay the flush req after is done

#=========================================================================
# BlockingCacheCtrlRTL
#=========================================================================

class BlockingCacheCtrlRTL ( Component ):

  def construct( s, p ):

    # Constants (required for translation to work)

    associativity      = p.associativity
    clog_asso          = clog2( p.associativity )
    BitsAssoclog2      = p.BitsAssoclog2
    BitsClogNlines     = p.BitsClogNlines
    BitsTagWben        = p.BitsTagWben
    bitwidth_num_lines = p.bitwidth_num_lines
    BitsClogNlines     = p.BitsClogNlines

    #=====================================================================
    # Interface
    #=====================================================================

    s.cachereq_en   = InPort ()
    s.cachereq_rdy  = OutPort()

    s.cacheresp_en  = OutPort()
    s.cacheresp_rdy = InPort ()

    s.memreq_en     = OutPort()
    s.memreq_rdy    = InPort ()

    s.memresp_en    = InPort ()
    s.memresp_rdy   = OutPort()

    s.status        = InPort ( p.StructStatus )
    s.ctrl          = OutPort( p.StructCtrl )

    #=====================================================================
    # Y Stage
    #=====================================================================

    # In Y stage we always set the memresp_rdy to high since we assume
    # there would be no memresp unless we have sent a memreq
    s.memresp_rdy //= y

    #=====================================================================
    # M0 Stage
    #=====================================================================

    s.memresp_en_M0 = m = RegEnRst( Bits1 )
    m.in_ //= s.memresp_en
    m.en  //= s.ctrl.reg_en_M0
    

    # Checks if memory response if valid
    s.memresp_val_M0 = Wire()
    s.memresp_val_M0 //= lambda: s.memresp_en_M0.out & ( s.status.memresp_type_M0 != WRITE )

    # Write Ack from memresp
    s.memresp_wr_ack_M0 = Wire()
    s.memresp_wr_ack_M0 //= lambda: s.memresp_en_M0.out & ( s.status.memresp_type_M0 == WRITE )

    # A counter used by FSM
    s.counter_M0 = CounterEnRst( p.BitsClogNlines,
                                 reset_value=( p.total_num_cachelines - 1 ) )
    s.update_way_idx_M0 = Wire( BitsClogNlines )

    # We need to update the dirty bits, set in M1 stage.
    s.is_write_hit_clean_M0 = Wire()

    # Flush-related singal
    s.has_flush_sent_M1_bypass  = Wire()
    s.no_flush_needed_M1_bypass = Wire()
    s.flush_refill_M1_bypass    = Wire()
    s.prev_flush_done_M0        = Wire()

    s.prev_flush_done_M0 //= lambda: (s.no_flush_needed_M1_bypass | s.memresp_wr_ack_M0 
                                    | s.flush_refill_M1_bypass )

    #---------------------------------------------------------------------
    # M0 stage FSM
    #---------------------------------------------------------------------

    s.FSM_state_M0_next = Wire( mk_bits(M0_FSM_STATE_NBITS) )
    s.FSM_state_M0 = m = RegEnRst( mk_bits(M0_FSM_STATE_NBITS), reset_value=M0_FSM_STATE_INIT )
    m.in_ //= s.FSM_state_M0_next
    m.en  //= s.ctrl.reg_en_M0
    
    # Next state logic
    @update
    def fsm_M0_next_state():
      s.FSM_state_M0_next @= M0_FSM_STATE_INIT
      
      if   s.FSM_state_M0.out == M0_FSM_STATE_INIT:
        if s.counter_M0.out == BitsClogNlines(0):
          s.FSM_state_M0_next @= M0_FSM_STATE_READY
        else:
          s.FSM_state_M0_next @= M0_FSM_STATE_INIT
      
      elif s.FSM_state_M0.out == M0_FSM_STATE_READY:
        if s.memresp_val_M0 & ((s.status.MSHR_type == WRITE) | (s.status.MSHR_type == READ)):
          # Have valid replays in the MSHR
          s.FSM_state_M0_next @= M0_FSM_STATE_REPLAY
        elif ( s.status.MSHR_empty & s.cachereq_en ):
          if s.status.cachereq_type_M0 == INV:
            s.FSM_state_M0_next @= M0_FSM_STATE_INV
          elif s.status.cachereq_type_M0 == FLUSH:
            s.FSM_state_M0_next @= M0_FSM_STATE_FLUSH
          else:
            s.FSM_state_M0_next @= M0_FSM_STATE_READY
        else:
          s.FSM_state_M0_next @= M0_FSM_STATE_READY
      
      elif s.FSM_state_M0.out == M0_FSM_STATE_INV:
        if s.counter_M0.out == 0:
          s.FSM_state_M0_next @= M0_FSM_STATE_REPLAY
        else:
          s.FSM_state_M0_next @= M0_FSM_STATE_INV
      
      elif s.FSM_state_M0.out == M0_FSM_STATE_REPLAY:
        # For flush we need to wait for the final write_ack
        if (~s.status.MSHR_empty) & (s.status.MSHR_type == FLUSH):
          if s.prev_flush_done_M0:
            s.FSM_state_M0_next @= M0_FSM_STATE_READY
          else:
            s.FSM_state_M0_next @= M0_FSM_STATE_FLUSH_WAIT
        # MSHR will be dealloc this cycle
        else:
          s.FSM_state_M0_next @= M0_FSM_STATE_READY
      
      elif s.FSM_state_M0.out == M0_FSM_STATE_FLUSH:
        if s.has_flush_sent_M1_bypass:
          s.FSM_state_M0_next @= M0_FSM_STATE_FLUSH_WAIT
        elif s.counter_M0.out == BitsClogNlines(0):
          s.FSM_state_M0_next @= M0_FSM_STATE_REPLAY
        else:
          s.FSM_state_M0_next @= M0_FSM_STATE_FLUSH
      
      elif s.FSM_state_M0.out == M0_FSM_STATE_FLUSH_WAIT:
        if s.memresp_wr_ack_M0:
          if s.counter_M0.out == trunc(Bits32(p.total_num_cachelines - 1), p.BitsClogNlines ):
            s.FSM_state_M0_next @= M0_FSM_STATE_REPLAY
          else:
            s.FSM_state_M0_next @= M0_FSM_STATE_FLUSH
        else:
          s.FSM_state_M0_next @= M0_FSM_STATE_FLUSH_WAIT

    #---------------------------------------------------------------------
    # M0 transaction
    #---------------------------------------------------------------------
    # Generate cache control transaction signal based on FSM state and
    # request type from cachereq or MSHR

    s.trans_M0 = Wire( mk_bits(TRANS_TYPE_NBITS) )

    @update
    def transaction_logic_M0():
      s.trans_M0 @= TRANS_TYPE_INVALID
      if s.FSM_state_M0.out == M0_FSM_STATE_INIT:
        s.trans_M0 @= TRANS_TYPE_CACHE_INIT
      elif s.is_write_hit_clean_M0:
        s.trans_M0 @= TRANS_TYPE_CLEAN_HIT
      elif s.FSM_state_M0.out == M0_FSM_STATE_REPLAY:
        if (~s.status.MSHR_empty) & (s.status.MSHR_type == WRITE):
          s.trans_M0 @= TRANS_TYPE_REPLAY_WRITE
        elif (~s.status.MSHR_empty) & (s.status.MSHR_type == READ):
          s.trans_M0 @= TRANS_TYPE_REPLAY_READ
        elif (~s.status.MSHR_empty) & (s.status.MSHR_type == INV):
          s.trans_M0 @= TRANS_TYPE_REPLAY_INV
        elif (~s.status.MSHR_empty) & (s.status.MSHR_type == FLUSH):
          if s.prev_flush_done_M0:
            s.trans_M0 @= TRANS_TYPE_REPLAY_FLUSH
          else:
            s.trans_M0 @= TRANS_TYPE_FLUSH_WAIT
      elif s.FSM_state_M0.out == M0_FSM_STATE_INV:
        s.trans_M0 @= TRANS_TYPE_INV_WRITE
      elif s.FSM_state_M0.out == M0_FSM_STATE_FLUSH:
        if s.has_flush_sent_M1_bypass:
          s.trans_M0 @= TRANS_TYPE_FLUSH_WAIT
        else:
          s.trans_M0 @= TRANS_TYPE_FLUSH_READ
      elif s.FSM_state_M0.out == M0_FSM_STATE_FLUSH_WAIT:
        if s.memresp_wr_ack_M0:
          s.trans_M0 @= TRANS_TYPE_FLUSH_WRITE
        else:
          s.trans_M0 @= TRANS_TYPE_FLUSH_WAIT
      elif s.FSM_state_M0.out == M0_FSM_STATE_READY:
        if s.memresp_val_M0 & (~s.status.MSHR_empty):
          if (s.status.MSHR_type == WRITE) | (s.status.MSHR_type == READ):
            s.trans_M0 @= TRANS_TYPE_REFILL
          elif ( (s.status.MSHR_type >= AMO_ADD) &
                 (s.status.MSHR_type <  INV) ):
            s.trans_M0 @= TRANS_TYPE_REPLAY_AMO

        elif s.status.MSHR_empty & s.cachereq_en:
          # Request from s.cachereq, not MSHR
          if s.status.cachereq_type_M0 == INIT:
            s.trans_M0 @= TRANS_TYPE_INIT_REQ
          elif s.status.cachereq_type_M0 == READ:
            s.trans_M0 @= TRANS_TYPE_READ_REQ
          elif s.status.cachereq_type_M0 == WRITE:
            s.trans_M0 @= TRANS_TYPE_WRITE_REQ
          elif ( (s.status.cachereq_type_M0 >= AMO_ADD) &
                 (s.status.cachereq_type_M0 < INV) ):
            s.trans_M0 @= TRANS_TYPE_AMO_REQ
          elif s.status.cachereq_type_M0 == INV:
            s.trans_M0 @= TRANS_TYPE_INV_START
          elif s.status.cachereq_type_M0 == FLUSH:
            s.trans_M0 @= TRANS_TYPE_FLUSH_START

    s.counter_en_M0 = Wire( Bits1 )

    @update
    def up_counter_en_logic_M0():
      s.counter_en_M0 @= b1(0)
      if ( (s.FSM_state_M0.out == M0_FSM_STATE_INIT) |
           (s.FSM_state_M0.out == M0_FSM_STATE_INV) ):
        s.counter_en_M0 @= b1(1)
      elif s.trans_M0 == TRANS_TYPE_FLUSH_READ:
        s.counter_en_M0 @= b1(1)

    s.counter_M0.count_down //= b1(1)
    s.counter_M0.en         //= lambda: s.ctrl.reg_en_M0 & s.counter_en_M0

    # When the flush ack come back, the counter has already been
    # decremented one extra time, so we need to add it back
    @update
    def update_way_idx_M0_loigc():
      s.update_way_idx_M0 @= s.counter_M0.out
      if ( ( s.trans_M0 == TRANS_TYPE_FLUSH_WRITE ) |
           ( s.trans_M0 == TRANS_TYPE_REPLAY_FLUSH ) ):
        s.update_way_idx_M0 @= s.counter_M0.out + BitsClogNlines(1)

    #---------------------------------------------------------------------
    # M0 control signals
    #---------------------------------------------------------------------
    # Control signals are generated based on transaction type and inputs

    # Stalls originating from M1 and M2
    s.ostall_M1 = Wire( Bits1 )
    s.ostall_M2 = Wire( Bits1 )

    s.stall_M0 = Wire( Bits1 )
    s.stall_M0 //= lambda: s.ostall_M1 | s.ostall_M2

    # We will select MSHR dealloc output instead of incoming cachereq if:
    # 1. We have a valid memresp ( we prioritize handling refills/replays )
    # 2. We are in a middle of a replay
    s.ctrl.cachereq_memresp_mux_sel_M0 //= lambda: (
        (s.FSM_state_M0.out == M0_FSM_STATE_REPLAY) | s.memresp_en_M0.out)

    # We will stall for the following conditions:
    # 1. We are initializing cache as a result of a reset
    # 2. We have a write hit to a clean cache line -> Tag array at M0 must
    # be updated with the correct dirty bit
    # 3. There is a stall in the cache due to external factors
    # 4. MSHR is not empty (for blocking cache)
    # 5. MSHR is full (for nonblocking cache)
    s.cachereq_rdy //= lambda: ~( (s.FSM_state_M0.out == M0_FSM_STATE_INIT) |
        s.is_write_hit_clean_M0 | s.stall_M0 | (~s.status.MSHR_empty ) |
        s.status.MSHR_full )

    #---------------------------------------------------------------------
    # M0 control signal table
    #---------------------------------------------------------------------

    s.cs0 = Wire( mk_bits( 9 + p.bitwidth_tag_wben ) )

    CS_tag_array_wben_M0     = slice( 9, 9 + p.bitwidth_tag_wben )
    CS_wdata_mux_sel_M0      = slice( 8, 9 )
    CS_addr_mux_sel_M0       = slice( 7, 8 )
    CS_tag_array_type_M0     = slice( 6, 7 )
    CS_tag_update_cmd_M0     = slice( 3, 6 )
    CS_tag_array_idx_sel_M0  = slice( 2, 3 )
    CS_update_tag_tag_sel_M0 = slice( 1, 2 )
    CS_mshr_dealloc_M0       = slice( 0, 1 )

    wben_val = concat( p.BitsVal(-1), p.BitsDirty(0), p.BitsTag(0) )
    wben_dty = concat( p.BitsVal(0), p.BitsDirty(-1), p.BitsTag(0) )

    @update
    def cs_table_M0():
      wben_none = BitsTagWben( 0 )  # not enable
      wben_all  = BitsTagWben( -1 ) # all-enable
      none      = UpdateTagArrayUnit_CMD_NONE
      clear     = UpdateTagArrayUnit_CMD_CLEAR
      wr_hit    = UpdateTagArrayUnit_CMD_WR_HIT
      wr_refill = UpdateTagArrayUnit_CMD_WR_REFILL
      rd_refill = UpdateTagArrayUnit_CMD_RD_REFILL
      inv       = UpdateTagArrayUnit_CMD_INV
      flush     = UpdateTagArrayUnit_CMD_FLUSH
      #                                                             tag_wben|wdat_mux|addr_mux|tg_ty|tag_update|tidx_sel|up_tag_sel|mshr_de
      s.cs0                                             @= concat( wben_none, b1(0),   b1(0),   rd,   none,      b1(0),   b1(0),     n )
      if   s.trans_M0 == TRANS_TYPE_CACHE_INIT:   s.cs0 @= concat( wben_all,  b1(0),   b1(0),   wr,   clear,     b1(1),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_REFILL:       s.cs0 @= concat( wben_all,  b1(1),   b1(0),   wr,   rd_refill, b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_REPLAY_READ:  s.cs0 @= concat( wben_dty,      x,   b1(0),   rd,   rd_refill, b1(0),   b1(0),     y )
      elif s.trans_M0 == TRANS_TYPE_REPLAY_WRITE: s.cs0 @= concat( wben_all,  b1(0),   b1(0),   wr,   wr_refill, b1(0),   b1(0),     y )
      elif s.trans_M0 == TRANS_TYPE_REPLAY_AMO:   s.cs0 @= concat( wben_all,  b1(1),   b1(0),   wr,   clear,     b1(0),   b1(0),     y )
      elif s.trans_M0 == TRANS_TYPE_CLEAN_HIT:    s.cs0 @= concat( wben_all,  b1(0),   b1(1),   wr,   wr_hit,    b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_INIT_REQ:     s.cs0 @= concat( wben_all,  b1(0),   b1(0),   wr,   rd_refill, b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_READ_REQ:     s.cs0 @= concat( wben_none, b1(0),   b1(0),   rd,   none,      b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_WRITE_REQ:    s.cs0 @= concat( wben_none, b1(0),   b1(0),   rd,   none,      b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_AMO_REQ:      s.cs0 @= concat( wben_none, b1(0),   b1(0),   rd,   none,      b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_INV_START:    s.cs0 @= concat( wben_none, b1(0),   b1(0),   rd,   none,      b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_INV_WRITE:    s.cs0 @= concat( wben_val,  b1(0),   b1(0),   wr,   inv,       b1(1),   b1(1),     n )
      elif s.trans_M0 == TRANS_TYPE_REPLAY_INV:   s.cs0 @= concat( wben_val,  b1(0),   b1(0),   wr,   inv,       b1(1),   b1(1),     y )
      elif s.trans_M0 == TRANS_TYPE_FLUSH_START:  s.cs0 @= concat( wben_none, b1(0),   b1(0),   rd,   none,      b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_FLUSH_READ:   s.cs0 @= concat( wben_none, b1(0),   b1(0),   rd,   none,      b1(1),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_FLUSH_WAIT:   s.cs0 @= concat( wben_none, b1(0),   b1(0),   rd,   none,      b1(0),   b1(0),     n )
      elif s.trans_M0 == TRANS_TYPE_FLUSH_WRITE:  s.cs0 @= concat( wben_dty,  b1(0),   b1(0),   wr,   flush,     b1(1),   b1(1),     n )
      elif s.trans_M0 == TRANS_TYPE_REPLAY_FLUSH: s.cs0 @= concat( wben_dty,  b1(0),   b1(0),   wr,   flush,     b1(1),   b1(1),     y )

      s.ctrl.tag_array_wben_M0    @= s.cs0[ CS_tag_array_wben_M0     ]
      s.ctrl.wdata_mux_sel_M0     @= s.cs0[ CS_wdata_mux_sel_M0      ]
      s.ctrl.addr_mux_sel_M0      @= s.cs0[ CS_addr_mux_sel_M0       ]
      s.ctrl.tag_array_type_M0    @= s.cs0[ CS_tag_array_type_M0     ]
      s.ctrl.update_tag_cmd_M0    @= s.cs0[ CS_tag_update_cmd_M0     ]
      s.ctrl.tag_array_idx_sel_M0 @= s.cs0[ CS_tag_array_idx_sel_M0  ]
      s.ctrl.update_tag_sel_M0    @= s.cs0[ CS_update_tag_tag_sel_M0 ]
      s.ctrl.MSHR_dealloc_en      @= s.cs0[ CS_mshr_dealloc_M0       ] & ~s.stall_M0

    s.ctrl.reg_en_M0 //= lambda: ~s.stall_M0
    # use higher bits of the counter to select index
    s.ctrl.tag_array_init_idx_M0 //= lambda: s.update_way_idx_M0[ clog_asso : bitwidth_num_lines ]
    s.ctrl.is_amo_M0 //= lambda: (( s.trans_M0 == TRANS_TYPE_REPLAY_AMO ) |
                                  ( s.trans_M0 == TRANS_TYPE_AMO_REQ ))

    @update
    def tag_array_val_logic_M0():
      # Most of the logic is for associativity > 1; should simplify for dmapped
      s.ctrl.update_tag_way_M0 @= BitsAssoclog2(0)
      for i in range( associativity ):
        s.ctrl.tag_array_val_M0[i] @= n # by default all tag arrays accesses are invalid
      if ( (s.trans_M0 == TRANS_TYPE_CACHE_INIT) |
           (s.trans_M0 == TRANS_TYPE_INV_WRITE) |
           (s.trans_M0 == TRANS_TYPE_REPLAY_INV) |
           (s.trans_M0 == TRANS_TYPE_FLUSH_READ) |
           (s.trans_M0 == TRANS_TYPE_FLUSH_WRITE) |
           (s.trans_M0 == TRANS_TYPE_REPLAY_FLUSH) ):
        # use lower bits of the counter to select ways
        for i in range( associativity ):
          if s.update_way_idx_M0 % BitsClogNlines(associativity) == BitsClogNlines(i):
            s.ctrl.tag_array_val_M0[i] @= y
            s.ctrl.update_tag_way_M0 @= BitsAssoclog2(i)
      elif ( (s.trans_M0 == TRANS_TYPE_REFILL) |
             (s.trans_M0 == TRANS_TYPE_REPLAY_WRITE) ):
        s.ctrl.tag_array_val_M0[s.status.MSHR_ptr] @= y
      elif (s.trans_M0 == TRANS_TYPE_REPLAY_AMO) & (s.status.amo_hit_M0):
        s.ctrl.tag_array_val_M0[s.status.MSHR_ptr] @= y
      elif s.trans_M0 == TRANS_TYPE_INIT_REQ:
        s.ctrl.tag_array_val_M0[s.status.ctrl_bit_rep_rd_M1] @= y
      elif s.trans_M0 == TRANS_TYPE_CLEAN_HIT:
        s.ctrl.tag_array_val_M0[s.status.hit_way_M1] @= y
      elif ( (s.trans_M0 == TRANS_TYPE_READ_REQ) |
             (s.trans_M0 == TRANS_TYPE_WRITE_REQ) |
             (s.trans_M0 == TRANS_TYPE_AMO_REQ) ):
        for i in range( associativity ):
          s.ctrl.tag_array_val_M0[i] @= y # Enable all SRAMs since we are reading

    #=====================================================================
    # M1 Stage
    #=====================================================================
    s.ctrl_pipeline_reg_en_M1 = Wire( Bits1 )
    s.trans_M1 = m = RegEnRst( mk_bits(TRANS_TYPE_NBITS) )
    m.in_ //= s.trans_M0
    m.en  //= s.ctrl_pipeline_reg_en_M1

    # Indicates which way in the cache to replace. We receive the value from
    # dealloc in the M0 stage and use it in both M0 and M1
    s.way_ptr_M1 = m = RegEnRst( p.BitsAssoclog2 )
    m.in_ //= s.status.MSHR_ptr
    m.en  //= s.ctrl_pipeline_reg_en_M1

    s.update_tag_way_M1 = m = RegEnRst( p.BitsAssoclog2 )
    m.in_ //= s.ctrl.update_tag_way_M0
    m.en  //= s.ctrl_pipeline_reg_en_M1

    s.hit_M1            = Wire( Bits1 )
    s.is_evict_M1       = Wire( Bits1 )
    s.stall_M1          = Wire( Bits1 )
    s.is_dty_M1         = Wire( Bits1 )
    # EXTRA Logic for accounting for set associative caches
    s.repreq_en_M1      = Wire( Bits1 )
    s.repreq_is_hit_M1  = Wire( Bits1 )
    s.repreq_hit_ptr_M1 = Wire( p.BitsAssoclog2 )

    s.stall_M1 //= lambda: s.ostall_M1 | s.ostall_M2

    # TODO: Need more work
    s.replacement_M1 = m = ReplacementPolicy( p.BitsAssoc, p.BitsAssoclog2, associativity, 0)
    m.repreq_en      //= s.repreq_en_M1
    m.repreq_hit_ptr //= s.repreq_hit_ptr_M1
    m.repreq_is_hit  //= s.repreq_is_hit_M1
    m.repreq_ptr     //= s.status.ctrl_bit_rep_rd_M1 # Read replacement mask
    m.represp_ptr    //= s.ctrl.ctrl_bit_rep_wr_M0   # Bypass to M0 stage?
    

    # Selects the index offset for the Data array based on which way to
    # read/write. We only use one data array and we have offset the index
    @update
    def asso_data_array_offset_way_M1():
      s.ctrl.way_offset_M1 @= s.status.hit_way_M1
      if ( (s.trans_M1.out == TRANS_TYPE_REPLAY_READ) |
           (s.trans_M1.out == TRANS_TYPE_REPLAY_WRITE) |
           (s.trans_M1.out == TRANS_TYPE_REFILL) ):
        s.ctrl.way_offset_M1 @= s.way_ptr_M1.out
      elif ( (s.trans_M1.out == TRANS_TYPE_READ_REQ) |
             (s.trans_M1.out == TRANS_TYPE_WRITE_REQ) ):
        if ~s.hit_M1:
          if s.status.inval_hit_M1:
            s.ctrl.way_offset_M1 @= s.status.hit_way_M1
          else:
            s.ctrl.way_offset_M1 @= s.status.ctrl_bit_rep_rd_M1
      elif s.trans_M1.out == TRANS_TYPE_AMO_REQ:
        s.ctrl.way_offset_M1 @= s.status.amo_hit_way_M1
      elif ( (s.trans_M1.out == TRANS_TYPE_FLUSH_READ) |
             (s.trans_M1.out == TRANS_TYPE_CACHE_INIT) ):
        s.ctrl.way_offset_M1 @= s.update_tag_way_M1.out

    s.flush_refill_M1_bypass //= lambda: s.trans_M1.out == TRANS_TYPE_FLUSH_WRITE

    @update
    def up_flush_tag_read_logic_M1():
      s.no_flush_needed_M1_bypass @= b1(0)
      s.has_flush_sent_M1_bypass  @= b1(0)
      if s.trans_M1.out == TRANS_TYPE_FLUSH_READ:
        if s.status.ctrl_bit_dty_rd_line_M1[ s.update_tag_way_M1.out ]:
          s.no_flush_needed_M1_bypass @= b1(0)
          s.has_flush_sent_M1_bypass  @= b1(1)
        else:
          s.no_flush_needed_M1_bypass @= b1(1)
          s.has_flush_sent_M1_bypass  @= b1(0)

    #---------------------------------------------------------------------
    # M1 status
    #---------------------------------------------------------------------
    # Determines the status in the M1 stage, such as hit/miss/evict

    @update
    def status_logic_M1():
      s.is_evict_M1       @= n
      s.is_dty_M1         @= s.status.ctrl_bit_dty_rd_line_M1[s.status.ctrl_bit_rep_rd_M1]
      # Bits for set associative caches
      s.repreq_is_hit_M1  @= n
      s.repreq_en_M1      @= n
      s.repreq_hit_ptr_M1 @= x
      s.hit_M1            @= n
      s.is_write_hit_clean_M0 @= n

      if ( (s.trans_M1.out == TRANS_TYPE_INIT_REQ) |
           (s.trans_M1.out == TRANS_TYPE_WRITE_REQ)|
           (s.trans_M1.out == TRANS_TYPE_READ_REQ) ):
        s.hit_M1 @= s.status.hit_M1
        # if hit, dty bit will come from the way where the hit occured
        if s.hit_M1:
          s.is_dty_M1 @= s.status.ctrl_bit_dty_rd_word_M1[s.status.hit_way_M1]

        if s.trans_M1.out == TRANS_TYPE_INIT_REQ:
          s.repreq_en_M1      @= y
          s.repreq_is_hit_M1  @= n

        # Check that we don't have a situation where ~val and dty but we're
        # still accessing the same address.
        if ~s.status.inval_hit_M1:
          # moyang: we are not check s.is_line_valid_M1 because for invalid
          # but dirty cache lines (due to cache invalidation), we still need
          # to evict them
          if ~s.hit_M1 & s.is_dty_M1:
            s.is_evict_M1 @= y
          elif s.hit_M1 & ~s.is_dty_M1:
            if s.trans_M1.out == TRANS_TYPE_WRITE_REQ:
              s.is_write_hit_clean_M0 @= y

        if ~s.is_evict_M1:
          # Better to update replacement bit right away because we need it
          # for nonblocking capability. For blocking, we can also update
          # during a refill for misses
          s.repreq_en_M1      @= y
          s.repreq_hit_ptr_M1 @= s.status.hit_way_M1
          s.repreq_is_hit_M1  @= s.hit_M1 | s.status.inval_hit_M1

      elif s.trans_M1.out == TRANS_TYPE_AMO_REQ:
        s.hit_M1 @= s.status.hit_M1
        s.is_dty_M1 @= s.status.ctrl_bit_dty_rd_line_M1[s.status.hit_way_M1]
        s.is_evict_M1 @= s.is_dty_M1 & ( s.hit_M1 | s.status.inval_hit_M1 )
        if s.hit_M1 | s.status.inval_hit_M1:
          s.repreq_en_M1      @= y
          s.repreq_hit_ptr_M1 @= ~s.status.hit_way_M1
          s.repreq_is_hit_M1  @= y

      s.ctrl.ctrl_bit_rep_en_M1 @= s.repreq_en_M1 & ~s.stall_M2

    s.was_stalled = m = RegRst( Bits1 )
    m.in_ //= s.ostall_M2
    s.evict_bypass = Wire( Bits1 )

    s.ctrl.tag_processing_en_M1 //= lambda: ((~s.is_evict_M2.out) & 
                                             (s.trans_M1.out!=TRANS_TYPE_INVALID)) 

    #---------------------------------------------------------------------
    # M1 control signal table
    #---------------------------------------------------------------------

    s.cs1 = Wire( mk_bits( 7 ) )
    CS_data_array_wben_M1 = slice( 5, 7 )
    CS_data_array_type_M1 = slice( 4, 5 )
    CS_data_array_val_M1  = slice( 3, 4 )
    CS_ostall_M1          = slice( 2, 3 )
    CS_evict_mux_sel_M1   = slice( 1, 2 )
    CS_MSHR_alloc_en      = slice( 0, 1 )
    @update
    def cs_table_M1():
      none = WriteBitEnGen_CMD_NONE
      req  = WriteBitEnGen_CMD_REQ
      dty  = WriteBitEnGen_CMD_DIRTY
      flush = s.has_flush_sent_M1_bypass
      #                                                                wben |ty |val    |ostall|evict mux|alloc_en
      s.cs1                                                 @= concat( none, x , n,      n,     b1(0),    n       )
      if   s.trans_M1.out == TRANS_TYPE_INVALID:      s.cs1 @= concat( none, x , n,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_CACHE_INIT:   s.cs1 @= concat(  dty, wr, y,      n,     b1(1),    n       )
      elif s.trans_M1.out == TRANS_TYPE_REFILL:       s.cs1 @= concat(  dty, wr, y,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_REPLAY_READ:  s.cs1 @= concat( none, rd, y,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_REPLAY_WRITE: s.cs1 @= concat(  req, wr, y,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_REPLAY_AMO:   s.cs1 @= concat( none, x , n,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_REPLAY_INV:   s.cs1 @= concat( none, x , n,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_CLEAN_HIT:    s.cs1 @= concat( none, x , n,      n,     b1(0),    n       )
      elif s.is_evict_M1:                             s.cs1 @= concat( none, rd, y,      y,     b1(1),    y       )
      elif s.trans_M1.out == TRANS_TYPE_INIT_REQ:     s.cs1 @= concat(  req, wr, y,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_AMO_REQ:      s.cs1 @= concat( none, x , n,      n,     b1(0),    y       )
      elif s.trans_M1.out == TRANS_TYPE_INV_START:    s.cs1 @= concat( none, x , n,      n,     b1(0),    y       )
      elif s.trans_M1.out == TRANS_TYPE_INV_WRITE:    s.cs1 @= concat( none, x , n,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_FLUSH_START:  s.cs1 @= concat( none, x , n,      n,     b1(0),    y       )
      elif s.trans_M1.out == TRANS_TYPE_FLUSH_READ:   s.cs1 @= concat( none, x , flush,  n,     b1(1),    n       )
      elif s.trans_M1.out == TRANS_TYPE_FLUSH_WAIT:   s.cs1 @= concat( none, x , n,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_FLUSH_WRITE:  s.cs1 @= concat( none, x , n,      n,     b1(0),    n       )
      elif s.trans_M1.out == TRANS_TYPE_REPLAY_FLUSH: s.cs1 @= concat( none, x , n,      n,     b1(0),    n       )
      elif ~s.hit_M1:                                 s.cs1 @= concat( none, x , n,      n,     b1(0),    y       )
      elif s.hit_M1:
        if   s.trans_M1.out == TRANS_TYPE_READ_REQ:   s.cs1 @= concat( none, rd, y,      n,     b1(0),    n       )
        elif s.trans_M1.out == TRANS_TYPE_WRITE_REQ:  s.cs1 @= concat(  req, wr, y,      n,     b1(0),    n       )

      s.ctrl.wben_cmd_M1        @= s.cs1[ CS_data_array_wben_M1 ]
      s.ctrl.data_array_type_M1 @= s.cs1[ CS_data_array_type_M1 ]
      s.ctrl.data_array_val_M1  @= s.cs1[ CS_data_array_val_M1  ]
      s.ostall_M1               @= s.cs1[ CS_ostall_M1          ]
      s.ctrl.evict_mux_sel_M1   @= s.cs1[ CS_evict_mux_sel_M1   ]
      s.ctrl.MSHR_alloc_en      @= s.cs1[ CS_MSHR_alloc_en      ] & ~s.stall_M1

    # Logic for pipelined registers for dpath
    s.ctrl.reg_en_M1 //= lambda: (~s.stall_M1 & ~s.is_evict_M1 &
        (s.trans_M0 != TRANS_TYPE_CACHE_INIT))

    # Logic for pipelined registers for ctrl
    s.ctrl_pipeline_reg_en_M1 //= lambda: (s.ctrl.reg_en_M1 |
        (s.trans_M0 == TRANS_TYPE_CACHE_INIT))

    # Logic for the SRAM tag array as a result of a stall in cache since the
    # values from the SRAM are valid for one cycle
    s.ctrl.stall_reg_en_M1      //= lambda: ~s.was_stalled.out
    s.ctrl.hit_stall_eng_en_M1  //= lambda: ~s.was_stalled.out & ~s.evict_bypass
    s.ctrl.is_init_M1           //= lambda: s.trans_M1.out == TRANS_TYPE_INIT_REQ

    # Flush transaction
    s.ctrl.flush_init_reg_en_M1 //= lambda: s.ctrl_pipeline_reg_en_M1
    s.ctrl.flush_idx_mux_sel_M1 //= lambda: (
      (s.trans_M1.out == TRANS_TYPE_FLUSH_READ) |
      (s.trans_M1.out == TRANS_TYPE_CACHE_INIT))

    # MSHR mask for the dirty bit; if we have an evict, then the dirty bits
    # stored in the MSHR is all 0 else we store the dirty bits in MSHR
    maskf = p.BitsDirty( -1 ) # need this for translation
    s.ctrl.dirty_evict_mask_M1 //= lambda: p.BitsDirty(0) if s.is_evict_M1 else maskf

    #=====================================================================
    # M2 Stage
    #=====================================================================

    s.ctrl_pipeline_reg_en_M2 = Wire( Bits1 )
    s.trans_M2 = m = RegEnRst( mk_bits(TRANS_TYPE_NBITS) )
    m.in_ //= s.trans_M1.out
    m.en  //= s.ctrl_pipeline_reg_en_M2

    s.is_evict_M2 = m = RegEnRst( Bits1 )
    m.in_ //= s.is_evict_M1
    m.en  //= s.ctrl_pipeline_reg_en_M2
    
    s.evict_bypass //= s.is_evict_M2.out

    s.hit_reg_M2 = m = RegEnRst( Bits1 )
    m.in_ //= s.hit_M1
    m.en  //= s.ctrl_pipeline_reg_en_M2
    m.out //= s.ctrl.hit_M2[0]
    
    s.has_flush_sent_M2 = m = RegEnRst( Bits1 )
    m.in_ //= s.has_flush_sent_M1_bypass
    m.en  //= s.ctrl_pipeline_reg_en_M2

    s.stall_M2  = Wire( Bits1 )
    s.stall_M2 //= s.ostall_M2

    #---------------------------------------------------------------------
    # M2 control signal table
    #---------------------------------------------------------------------

    s.cs2 = Wire( Bits9 )

    CS_data_size_mux_en_M2  = slice( 8,  9 )
    CS_read_data_mux_sel_M2 = slice( 7,  8 )
    CS_ostall_M2            = slice( 6,  7 )
    CS_memreq_type          = slice( 2,  6 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )

    @update
    def cs_table_M2():
      flush = s.has_flush_sent_M2.out
      #                                                                dsize_en|rdata_mux|ostall|memreq_type|memreq|cacheresp
      s.cs2                                                 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      if   s.trans_M2.out == TRANS_TYPE_INVALID:      s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      elif s.trans_M2.out == TRANS_TYPE_CACHE_INIT:   s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      elif s.trans_M2.out == TRANS_TYPE_INV_START:    s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      elif s.trans_M2.out == TRANS_TYPE_INV_WRITE:    s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      elif s.trans_M2.out == TRANS_TYPE_CLEAN_HIT:    s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      elif s.trans_M2.out == TRANS_TYPE_FLUSH_START:  s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      elif s.trans_M2.out == TRANS_TYPE_FLUSH_WAIT:   s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      elif s.trans_M2.out == TRANS_TYPE_FLUSH_WRITE:  s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     n        )
      elif ~s.memreq_rdy|~s.cacheresp_rdy:            s.cs2 @= concat( n,       b1(0),    y,     READ,       n,     n        )
      elif s.trans_M2.out == TRANS_TYPE_FLUSH_READ:   s.cs2 @= concat( n,       b1(0),    n,     WRITE,      flush, n        )
      elif s.is_evict_M2.out:                         s.cs2 @= concat( n,       b1(0),    n,     WRITE,      y,     n        )
      elif s.trans_M2.out == TRANS_TYPE_REPLAY_READ:  s.cs2 @= concat( y,       b1(0),    n,     READ,       n,     y        )
      elif s.trans_M2.out == TRANS_TYPE_REPLAY_WRITE: s.cs2 @= concat( n,       b1(0),    n,     WRITE,      n,     y        )
      elif s.trans_M2.out == TRANS_TYPE_REPLAY_AMO:   s.cs2 @= concat( n,       b1(1),    n,     READ,       n,     y        )
      elif s.trans_M2.out == TRANS_TYPE_REPLAY_INV:   s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     y        )
      elif s.trans_M2.out == TRANS_TYPE_REPLAY_FLUSH: s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     y        )
      elif s.trans_M2.out == TRANS_TYPE_INIT_REQ:     s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     y        )
      elif s.trans_M2.out == TRANS_TYPE_AMO_REQ:      s.cs2 @= concat( n,       b1(1),    n,     AMO,        y,     n        )
      elif s.trans_M2.out == TRANS_TYPE_READ_REQ:
        if    s.ctrl.hit_M2[0]:                       s.cs2 @= concat( y,       b1(0),    n,     READ,       n,     y        )
        elif ~s.ctrl.hit_M2[0]:                       s.cs2 @= concat( n,       b1(0),    n,     READ,       y,     n        )
      elif s.trans_M2.out == TRANS_TYPE_WRITE_REQ:
        if  s.ctrl.hit_M2[0]:                         s.cs2 @= concat( n,       b1(0),    n,     READ,       n,     y        )
        elif ~s.ctrl.hit_M2[0]:                       s.cs2 @= concat( n,       b1(0),    n,     READ,       y,     n        )

      s.ctrl.data_size_mux_en_M2  @= s.cs2[ CS_data_size_mux_en_M2  ]
      s.ctrl.read_data_mux_sel_M2 @= s.cs2[ CS_read_data_mux_sel_M2 ]
      s.ostall_M2                 @= s.cs2[ CS_ostall_M2            ]
      if s.cs2[ CS_memreq_type ] >= AMO:
        s.ctrl.memreq_type        @= s.status.cachereq_type_M2
      else:
        s.ctrl.memreq_type        @= s.cs2[ CS_memreq_type          ]
      s.cacheresp_en              @= s.cs2[ CS_cacheresp_en         ]
      s.memreq_en                 @= s.cs2[ CS_memreq_en            ]

    # dpath pipeline reg en; will only en if we have a stall in M2 and if
    # we are not initing the cache since that is entirely internal
    # We can likely not need to stall for inv also
    s.ctrl.reg_en_M2 //= lambda: ( ( ~s.stall_M2 ) & ( s.trans_M1.out != 
                                                      TRANS_TYPE_CACHE_INIT ) )
    # ctrl pipeline reg en; We will enable ctrl during cache init even during
    # an external stall since the transaction is entirely internal
    s.ctrl_pipeline_reg_en_M2 //= lambda: ( s.ctrl.reg_en_M2 | ( s.trans_M1.out 
                                                      == TRANS_TYPE_CACHE_INIT ) )

    s.ctrl.stall_reg_en_M2 //= lambda: ~s.was_stalled.out

    # Set a flag for amo transaction
    s.ctrl.is_amo_M2 //= lambda: (
      ( (s.trans_M2.out == TRANS_TYPE_AMO_REQ) |
        (s.trans_M2.out == TRANS_TYPE_REPLAY_AMO) ) &
      (~s.is_evict_M2.out) )

    s.ctrl.hit_M2[1] //= 0 # hit output expects 2 bits but we only use one bit

  #=======================================================================
  # line_trace
  #=======================================================================

  def line_trace( s ):

    msg_M0 = ""
    if s.FSM_state_M0.out == M0_FSM_STATE_INIT:
      msg_M0 = "(init)"
    elif s.FSM_state_M0.out == M0_FSM_STATE_READY:
      msg_M0 = "(rdy )"
    elif s.FSM_state_M0.out == M0_FSM_STATE_REPLAY:
      msg_M0 = "(rpy )"
    elif s.FSM_state_M0.out == M0_FSM_STATE_INV:
      msg_M0 = "(inv )"
    elif s.FSM_state_M0.out == M0_FSM_STATE_FLUSH:
      msg_M0 = "(flsh)"
    elif s.FSM_state_M0.out == M0_FSM_STATE_FLUSH_WAIT:
      msg_M0 = "(fls#)"
    else:
      assert False
    # msg_M0 += ",cnt={} ".format(s.update_way_idx_M0)

    if s.trans_M0 == TRANS_TYPE_INVALID:        msg_M0 += "xxx"
    elif s.trans_M0 == TRANS_TYPE_REFILL:       msg_M0 += " rf"
    elif s.trans_M0 == TRANS_TYPE_CLEAN_HIT:    msg_M0 += " wc"
    elif s.trans_M0 == TRANS_TYPE_REPLAY_READ:  msg_M0 += "rpr"
    elif s.trans_M0 == TRANS_TYPE_REPLAY_WRITE: msg_M0 += "rpw"
    elif s.trans_M0 == TRANS_TYPE_READ_REQ:     msg_M0 += " rd"
    elif s.trans_M0 == TRANS_TYPE_WRITE_REQ:    msg_M0 += " wr"
    elif s.trans_M0 == TRANS_TYPE_INIT_REQ:     msg_M0 += " in"
    elif s.trans_M0 == TRANS_TYPE_CACHE_INIT:   msg_M0 += "ini"
    elif s.trans_M0 == TRANS_TYPE_AMO_REQ:      msg_M0 += "amo"
    elif s.trans_M0 == TRANS_TYPE_REPLAY_AMO:   msg_M0 += "rpa"
    elif s.trans_M0 == TRANS_TYPE_INV_WRITE:    msg_M0 += "ivw"
    elif s.trans_M0 == TRANS_TYPE_INV_START:    msg_M0 += "iv0"
    elif s.trans_M0 == TRANS_TYPE_REPLAY_INV:   msg_M0 += "ivp"
    elif s.trans_M0 == TRANS_TYPE_FLUSH_START:  msg_M0 += "fl0"
    elif s.trans_M0 == TRANS_TYPE_FLUSH_READ:   msg_M0 += "flr"
    elif s.trans_M0 == TRANS_TYPE_FLUSH_WAIT:   msg_M0 += "fl#"
    elif s.trans_M0 == TRANS_TYPE_FLUSH_WRITE:  msg_M0 += "flw"
    elif s.trans_M0 == TRANS_TYPE_REPLAY_FLUSH: msg_M0 += "flp"
    else:                                       msg_M0 += "   "

    if not s.cachereq_rdy: msg_M0 = "#" + msg_M0
    else:                  msg_M0 = " " + msg_M0

    msg_M1 = "   "
    color_m1 = Back.BLACK + Fore.GREEN if s.hit_M1 else Back.BLACK + Fore.RED

    if s.trans_M1.out == TRANS_TYPE_REFILL:         msg_M1 = " rf"
    elif s.trans_M1.out == TRANS_TYPE_CLEAN_HIT:    msg_M1 = " wc"
    elif s.trans_M1.out == TRANS_TYPE_REPLAY_READ:  msg_M1 = "rpr"
    elif s.trans_M1.out == TRANS_TYPE_REPLAY_WRITE: msg_M1 = "rpw"
    elif s.trans_M1.out == TRANS_TYPE_READ_REQ:     msg_M1 = color_m1 + " rd" + Style.RESET_ALL
    elif s.trans_M1.out == TRANS_TYPE_WRITE_REQ:    msg_M1 = color_m1 + " wr" + Style.RESET_ALL
    elif s.trans_M1.out == TRANS_TYPE_INIT_REQ:     msg_M1 = " in"
    elif s.trans_M1.out == TRANS_TYPE_CACHE_INIT:   msg_M1 = "ini"
    elif s.trans_M1.out == TRANS_TYPE_AMO_REQ:      msg_M1 = "amo"
    elif s.trans_M1.out == TRANS_TYPE_REPLAY_AMO:   msg_M1 = "rpa"
    elif s.trans_M1.out == TRANS_TYPE_INV_WRITE:    msg_M1 = "ivw"
    elif s.trans_M1.out == TRANS_TYPE_INV_START:    msg_M1 = "iv0"
    elif s.trans_M1.out == TRANS_TYPE_REPLAY_INV:   msg_M1 = "ivp"
    elif s.trans_M1.out == TRANS_TYPE_FLUSH_START:  msg_M1 = "fl0"
    elif s.trans_M1.out == TRANS_TYPE_FLUSH_READ:   msg_M1 = "flr"
    elif s.trans_M1.out == TRANS_TYPE_FLUSH_WAIT:   msg_M1 = "fl#"
    elif s.trans_M1.out == TRANS_TYPE_FLUSH_WRITE:  msg_M1 = "frw"
    elif s.trans_M1.out == TRANS_TYPE_REPLAY_FLUSH: msg_M1 = "flp"

    msg_M2 = "   "
    if   s.trans_M2.out == TRANS_TYPE_REFILL:       msg_M2 = " rf"
    elif s.trans_M2.out == TRANS_TYPE_CLEAN_HIT:    msg_M2 = " wc"
    elif s.trans_M2.out == TRANS_TYPE_REPLAY_READ:  msg_M2 = "rpr"
    elif s.trans_M2.out == TRANS_TYPE_REPLAY_WRITE: msg_M2 = "rpw"
    elif s.is_evict_M2.out:                         msg_M2 = " ev"
    elif s.trans_M2.out == TRANS_TYPE_READ_REQ:     msg_M2 = " rd"
    elif s.trans_M2.out == TRANS_TYPE_WRITE_REQ:    msg_M2 = " wr"
    elif s.trans_M2.out == TRANS_TYPE_INIT_REQ:     msg_M2 = " in"
    elif s.trans_M2.out == TRANS_TYPE_CACHE_INIT:   msg_M2 = "ini"
    elif s.trans_M2.out == TRANS_TYPE_AMO_REQ:      msg_M2 = "amo"
    elif s.trans_M2.out == TRANS_TYPE_REPLAY_AMO:   msg_M2 = "rpa"
    elif s.trans_M2.out == TRANS_TYPE_INV_WRITE:    msg_M2 = "ivw"
    elif s.trans_M2.out == TRANS_TYPE_INV_START:    msg_M2 = "iv0"
    elif s.trans_M2.out == TRANS_TYPE_REPLAY_INV:   msg_M2 = "ivp"
    elif s.trans_M2.out == TRANS_TYPE_FLUSH_START:  msg_M2 = "fl0"
    elif s.trans_M2.out == TRANS_TYPE_FLUSH_READ:   msg_M2 = "flr"
    elif s.trans_M2.out == TRANS_TYPE_FLUSH_WAIT:   msg_M2 = "fl#"
    elif s.trans_M2.out == TRANS_TYPE_FLUSH_WRITE:  msg_M2 = "flw"
    elif s.trans_M2.out == TRANS_TYPE_REPLAY_FLUSH: msg_M2 = "flp"

    msg_memresp = ">" if s.memresp_en else " "
    msg_memreq = ">" if s.memreq_en else " "

    stage1 = "{}|{}".format(msg_memresp, msg_M0) if s.memresp_en else " |{}".format(msg_M0)
    stage2 = "|{}".format(msg_M1)
    stage3 = "|{}|{}".format(msg_M2, msg_memreq)
    pipeline = stage1 + stage2 + stage3

    add_msgs = ''
    # add_msgs += f'ev:{s.is_evict_M2.out} '
    # add_msgs += f'cn:{s.counter_M0.out} fsb:{s.has_flush_sent_M1_bypass} fd:{s.prev_flush_done_M0}'

    return pipeline + add_msgs

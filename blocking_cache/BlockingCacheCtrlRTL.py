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

class BlockingCacheCtrlRTL ( Component ):

  def construct( s, p ):
    
    # Constants (required for translation to work)
    associativity = p.associativity

    #--------------------------------------------------------------------------
    # Interface
    #--------------------------------------------------------------------------

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

    #--------------------------------------------------------------------------
    # Y Stage
    #--------------------------------------------------------------------------

    @s.update
    def mem_resp_rdy():
      s.memresp_rdy = y # Always yes

    #--------------------------------------------------------------------------
    # M0 Stage
    #---------------------------------------------------------------------------

    s.memresp_en_M0 = RegEnRst( Bits1 )( 
      in_ = s.memresp_en,
      en  = s.ctrl.reg_en_M0
    )

    s.MSHR_replay_next_M0 = Wire( Bits1 )
    s.MSHR_replay_reg_M0 = RegEnRst( Bits1 )(
      in_ = s.MSHR_replay_next_M0,
      en  = s.ctrl.reg_en_M0
    )

    s.state_M0 = Wire( p.CtrlMsg )
    s.memresp_val_M0 = Wire(Bits1)
    @s.update
    def replay_logic_M0():
      # Controls the refill/write_refill request generation
      # Also interfaces with the MSHR for replays
      # default values
      s.state_M0.is_refill = n
      s.state_M0.is_write_refill = n
      s.ctrl.MSHR_dealloc_en = n
      s.MSHR_replay_next_M0 = n
      s.memresp_val_M0 = n
      
      # Checks if memory response if valid
      if s.memresp_en_M0.out and s.status.memresp_type_M0 != WRITE:
        s.memresp_val_M0 = y
      
      # Combined FSM block
      if not s.MSHR_replay_reg_M0.out: 
        if s.memresp_val_M0:
          # Recv memresp that's not a write
          s.state_M0.is_refill = y         # Always refill first regardless
          if s.status.MSHR_type == READ: # If read, then we dealloc and run 
            s.ctrl.MSHR_dealloc_en = y # the read cachereq with the refill
          # Replay logic  
          if not s.status.MSHR_empty: # If we still have valid replays
            s.MSHR_replay_next_M0 = y   # in the MSHR, then we stall

      elif s.MSHR_replay_reg_M0.out: # replay state
        if not s.status.MSHR_empty: # If not empty, then we remain in 
          s.MSHR_replay_next_M0 = y   # this state. 
          s.ctrl.MSHR_dealloc_en = y  
          if s.status.MSHR_type == WRITE: # On a write, we will tell cache
            s.state_M0.is_write_refill = y  # that it is a write refill  
          elif s.status.MSHR_type == READ:
            s.state_M0.is_refill = y # regular refill on read

    
    s.stall_M0 = Wire(Bits1)     # stall signal for the M0 stage
    @s.update
    def cachereq_rdy_logic():
      s.cachereq_rdy = y #default yes
      if s.state_M0.is_write_hit_clean:
        s.cachereq_rdy = n
      elif s.stall_M0: # stall in the cache due to evict, stalls in M1 and M2
        s.cachereq_rdy = n
      elif s.status.MSHR_full or not s.status.MSHR_empty:
        # no space in MSHR or we have replay
        s.cachereq_rdy = n

    CS_tag_array_wben_M0  = slice( 5, 5 + p.bitwidth_tag_wben )
    CS_wdata_mux_sel_M0   = slice( 4, 5 )
    CS_addr_mux_sel_M0    = slice( 3, 4 )
    CS_memresp_mux_sel_M0 = slice( 2, 3 )
    CS_tag_array_type_M0  = slice( 1, 2 )
    CS_ctrl_bit_val_wr_M0 = slice( 0, 1 )

    s.cs0 = Wire( mk_bits( 5 + p.bitwidth_tag_wben ) ) # Bits for control signal table
    s.ostall_M0 = Wire(Bits1) 
    s.ostall_M1 = Wire(Bits1) # Stalls originating from earlier in pipeline
    s.ostall_M2 = Wire(Bits1) 
    tg_wbenf = p.tg_wbenf
    @s.update
    def comb_block_M0(): # logic block for setting output ports
      s.ostall_M0 = n  # Not sure if neccessary but include for completeness
      
      # valid cache states
      if s.cachereq_en or s.memresp_val_M0 or s.state_M0.is_write_refill or \
          s.state_M0.is_write_hit_clean:
        s.state_M0.val = y
      else: 
        s.state_M0.val = n
      
      #                tag_wben |wdat_mux|addr_mux|memrp_mux|tg_ty|dty|val
      s.cs0 = concat( tg_wbenf  , b1(0)  , b1(0)  ,    x    ,  rd , x , x ) # default value
      if s.state_M0.val: #                                             tag_wben|wdat_mux|addr_mux|memrp_mux|tg_ty|val
        if s.state_M0.is_refill:                       s.cs0 = concat( tg_wbenf, b1(1)  , b1(0)  , b1(1)   ,  wr , y )
        elif s.state_M0.is_write_refill:               s.cs0 = concat( tg_wbenf, b1(0)  , b1(0)  , b1(1)   ,  wr , y )
        elif s.state_M0.is_write_hit_clean:            s.cs0 = concat( tg_wbenf, b1(0)  , b1(1)  , b1(0)   ,  wr , y )
        else:
          if (s.status.cachereq_type_M0 == INIT):      s.cs0 = concat( tg_wbenf, b1(0)  , b1(0)  , b1(0)   ,  wr , y )
          elif (s.status.cachereq_type_M0 == READ):    s.cs0 = concat( tg_wbenf, b1(0)  , b1(0)  , b1(0)   ,  rd , n )
          elif (s.status.cachereq_type_M0 == WRITE):   s.cs0 = concat( tg_wbenf, b1(0)  , b1(0)  , b1(0)   ,  rd , n )

      s.ctrl.tag_array_wben_M0  = s.cs0[ CS_tag_array_wben_M0  ]
      s.ctrl.wdata_mux_sel_M0   = s.cs0[ CS_wdata_mux_sel_M0   ]
      s.ctrl.addr_mux_sel_M0    = s.cs0[ CS_addr_mux_sel_M0    ]
      s.ctrl.memresp_mux_sel_M0 = s.cs0[ CS_memresp_mux_sel_M0 ]
      s.ctrl.tag_array_type_M0  = s.cs0[ CS_tag_array_type_M0  ]
      s.ctrl.ctrl_bit_val_wr_M0 = s.cs0[ CS_ctrl_bit_val_wr_M0 ]
      # s.ctrl.ctrl_bit_dty_wr_M0 = s.cs0[ CS_ctrl_bit_dty_wr_M0 ]

      s.ctrl.is_write_refill_M0 = s.state_M0.is_write_refill
      s.ctrl.is_write_hit_clean_M0 = s.state_M0.is_write_hit_clean

      s.stall_M0  = s.ostall_M0 | s.ostall_M1 | s.ostall_M2
      s.ctrl.reg_en_M0 = ~s.stall_M0

      s.ctrl.ctrl_bit_dty_wr_M0 = s.status.new_dirty_bits_M0

    @s.update
    def tag_array_val_logic_M0():
      # Most of the logic is for associativity > 1; should simplify for dmapped
      for i in range( associativity ):
        s.ctrl.tag_array_val_M0[i] = n # Enable all SRAMs since we are reading
      if s.state_M0.val:
        if s.state_M0.is_refill:
          s.ctrl.tag_array_val_M0[s.status.MSHR_ptr] = y
        elif s.state_M0.is_write_refill:     
          s.ctrl.tag_array_val_M0[s.status.MSHR_ptr] = y      
        elif s.status.cachereq_type_M0 == INIT:
          s.ctrl.tag_array_val_M0[s.status.ctrl_bit_rep_rd_M1] = y
        elif s.state_M0.is_write_hit_clean:   
          s.ctrl.tag_array_val_M0[s.status.hit_way_M1] = y
        else:
          for i in range( associativity ):
            if s.status.cachereq_type_M0 == READ or s.status.cachereq_type_M0 == WRITE: 
              s.ctrl.tag_array_val_M0[i] = y # Enable all SRAMs since we are reading
            else:
              s.ctrl.tag_array_val_M0[i] = n
              
    #--------------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------------
    
    s.state_M1 = CtrlPipelineReg( p )(
      in_ = s.state_M0,
      en  = s.ctrl.reg_en_M1,
    )
    
    # Indicates which way in the cache to replace. We receive the value from 
    # dealloc in the M0 stage and use it in both M0 and M1
    s.way_ptr_M1 = RegEnRst( p.BitsAssoclog2 )(
      in_ = s.status.MSHR_ptr,
      en  = s.ctrl.reg_en_M1,
    )

    s.is_evict_M1 = Wire(Bits1)
    s.stall_M1  = Wire(Bits1)   
    # EXTRA Logic for accounting for set associative caches
    s.repreq_en_M1      = Wire(Bits1)
    s.repreq_is_hit_M1  = Wire(Bits1)
    s.repreq_hit_ptr_M1 = Wire(p.BitsAssoclog2)

    s.replacement_M1 = ReplacementPolicy(
      p.BitsAssoc, p.BitsAssoclog2, associativity, 0
    )(
      repreq_en       = s.repreq_en_M1,
      repreq_hit_ptr  = s.repreq_hit_ptr_M1,
      repreq_is_hit   = s.repreq_is_hit_M1,
      repreq_ptr      = s.status.ctrl_bit_rep_rd_M1, # Read replacement mask
      represp_ptr     = s.ctrl.ctrl_bit_rep_wr_M0,   # Bypass to M0 stage? 
      #TODO Need more work
    )

    @s.update
    def Asso_data_array_offset_way_M1():
      # Selects the index offset for the Data array based on which way to 
      # read/write. We only use one data array and we have offset the index
      s.ctrl.way_offset_M1 = s.status.hit_way_M1
      if s.state_M1.out.val:
        if s.state_M1.out.is_refill or s.state_M1.out.is_write_refill:
          s.ctrl.way_offset_M1 = s.way_ptr_M1.out
        elif s.status.hit_M1 or s.status.cachereq_type_M1 == INIT:
          s.ctrl.way_offset_M1 = s.status.hit_way_M1
        elif s.is_evict_M1:
          s.ctrl.way_offset_M1 = s.status.ctrl_bit_rep_rd_M1

    s.is_dty_M1 = Wire(Bits1)
    @s.update
    def status_logic_M1():
      # Determines the status of the M1 stage  
      s.is_evict_M1 = n
      s.state_M0.is_write_hit_clean = n # bypasses the write_hit_clean flag to M0
      # TODO Adjust is_dty_M1 to OR all word dirty bits
      s.is_dty_M1 = s.status.ctrl_bit_dty_rd_M1[s.status.ctrl_bit_rep_rd_M1]
      # Bits for set associative caches
      s.repreq_is_hit_M1  = n
      s.repreq_en_M1      = n
      s.repreq_hit_ptr_M1 = x
      
      if s.state_M1.out.val:
        if s.status.hit_M1: # if hit, dty bit will come from the way where the 
          # hit occured
          s.is_dty_M1 = s.status.ctrl_bit_dty_rd_M1[s.status.hit_way_M1]
        
        if not s.state_M1.out.is_refill and not s.state_M1.out.is_write_refill: 

          if s.status.cachereq_type_M1 == INIT:
            s.repreq_en_M1      = y
            s.repreq_is_hit_M1  = n   

          if not s.status.hit_M1 and s.is_dty_M1:
            s.is_evict_M1 = y
          elif s.status.hit_M1 and not s.status.ctrl_bit_dty_rd_M1[s.status.hit_way_M1]: 
            if not s.state_M1.out.is_write_hit_clean and \
              s.status.cachereq_type_M1 == WRITE:
              s.state_M0.is_write_hit_clean = y 

          if not s.is_evict_M1 and not s.state_M1.out.is_write_hit_clean:
            # Better to update replacement bit right away because we need it 
            # for nonblocking capability. For blocking, we can also update 
            # during a refill for misses
            s.repreq_en_M1      = y
            s.repreq_hit_ptr_M1 = s.status.hit_way_M1
            s.repreq_is_hit_M1  = s.status.hit_M1
            
      s.ctrl.ctrl_bit_rep_en_M1 = s.repreq_en_M1 & ~s.stall_M1
      s.ctrl.hit_M2[1]= b1(0) # hit output expects 2 bits but we only use one bit

    # Calculating shift amount
    # 0 -> 0x000f, 1 -> 0x00f0, 2 -> 0x0f00, 3 -> 0xf000
    s.wben_in    = Wire(p.BitsDataWben)
    BitsDataWben = p.BitsDataWben
    BitsLen      = p.BitsLen
    @s.update
    def mask_select_M1():
      if s.status.len_M1 == BitsLen(0):
        s.wben_in = BitsDataWben(data_array_word_mask)
      elif s.status.len_M1 == BitsLen(1):
        s.wben_in = BitsDataWben(data_array_byte_mask)
      elif s.status.len_M1 == BitsLen(2):
        s.wben_in = BitsDataWben(data_array_2byte_mask)
      else:
        s.wben_in = BitsDataWben(data_array_word_mask)
    s.WbenGen = LeftLogicalShifter( BitsDataWben, clog2(p.bitwidth_data_wben) )(
      in_ = s.wben_in,
      shamt = s.status.offset_M1,
    )

    CS_data_array_wben_M1 = slice( 5, 5 + p.bitwidth_data_wben )
    CS_data_array_type_M1 = slice( 4, 5 )
    CS_data_array_val_M1  = slice( 3, 4 )
    CS_ostall_M1          = slice( 2, 3 )
    CS_evict_mux_sel_M1   = slice( 1, 2 )
    CS_MSHR_alloc_en      = slice( 0, 1 )
    s.cs1 = Wire( mk_bits( 5 + p.bitwidth_data_wben ) )
    wben0 = p.BitsDataWben(0)
    wbenf = p.BitsDataWben(-1)
    @s.update
    def signal_select_logic_M1():
      wben  = s.WbenGen.out
      #              wben | ty|val|ostall|evict mux|alloc_en  
      s.cs1 = concat(wben0, x , n , n    , b1(0)   , n    )
      if s.state_M1.out.val: #                                       wben| ty|val|ostall|evict mux|alloc_en  
        if s.state_M1.out.is_refill:                 s.cs1 = concat(wbenf, wr, y , n    , b1(0)   ,   n   )
        elif s.state_M1.out.is_write_refill:         s.cs1 = concat( wben, wr, y , n    , b1(0)   ,   n   ) 
        elif s.state_M1.out.is_write_hit_clean:      s.cs1 = concat(wbenf, x , n , n    , b1(0)   ,   n   )
        elif s.is_evict_M1:                          s.cs1 = concat(wben0, rd, y , y    , b1(1)   ,   y   )
        else:
          if s.status.cachereq_type_M1 == INIT:      s.cs1 = concat( wben, wr, y , n    , b1(0)   ,   n   )
          elif ~s.status.hit_M1 and ~s.is_dty_M1:    s.cs1 = concat(wben0, x , n , n    , b1(0)   ,   y   )
          elif ~s.status.hit_M1 and  s.is_dty_M1:    s.cs1 = concat(wben0, x , n , n    , b1(0)   ,   y   )
          elif  s.status.hit_M1 and ~s.is_dty_M1:
            if   s.status.cachereq_type_M1 == READ:  s.cs1 = concat(wben0, rd, y , n    , b1(0)   ,   n   )
            elif s.status.cachereq_type_M1 == WRITE: s.cs1 = concat( wben, wr, y , n    , b1(0)   ,   n   )
          elif  s.status.hit_M1 and  s.is_dty_M1:
            if   s.status.cachereq_type_M1 == READ:  s.cs1 = concat(wben0, rd, y , n    , b1(0)   ,   n   )
            elif s.status.cachereq_type_M1 == WRITE: s.cs1 = concat( wben, wr, y , n    , b1(0)   ,   n   )

      s.ctrl.data_array_wben_M1 = s.cs1[ CS_data_array_wben_M1 ]
      s.ctrl.data_array_type_M1 = s.cs1[ CS_data_array_type_M1 ]
      s.ctrl.data_array_val_M1  = s.cs1[ CS_data_array_val_M1  ]
      s.ostall_M1                   = s.cs1[ CS_ostall_M1          ]
      s.stall_M1 = s.ostall_M1 | s.ostall_M2
      s.ctrl.evict_mux_sel_M1   = s.cs1[ CS_evict_mux_sel_M1   ]
      s.ctrl.MSHR_alloc_en      = s.cs1[ CS_MSHR_alloc_en      ] & ~s.stall_M1
      s.ctrl.reg_en_M1 = ~s.stall_M1 & ~s.is_evict_M1

    s.was_stalled = RegRst(Bits1)(
      in_ = s.ostall_M2,
    )

    @s.update
    def stall_logic_M1(): 
      # Logic for the SRAM tag array as a result of a stall in cache since the
      # values from the SRAM are valid for one cycle 
      s.ctrl.stall_mux_sel_M1 = s.was_stalled.out
      s.ctrl.stall_reg_en_M1  = ~s.was_stalled.out

    #--------------------------------------------------------------------------
    # M2 Stage
    #--------------------------------------------------------------------------
    
    s.state_M2 = CtrlPipelineReg( p )(
      en  = s.ctrl.reg_en_M2,
      in_ = s.state_M1.out,
    )

    s.is_evict_M2 = RegEnRst(Bits1)(
      in_ = s.is_evict_M1,
      en  = s.ctrl.reg_en_M2,
    )

    s.hit_reg_M2 = RegEnRst(Bits1)(
      in_ = s.status.hit_M1,
      en  = s.ctrl.reg_en_M2,
      out = s.ctrl.hit_M2[0],
    )

    CS_data_size_mux_en_M2  = slice( 8,  9 )
    CS_read_data_mux_sel_M2 = slice( 7,  8 )
    CS_ostall_M2            = slice( 6,  7 )
    CS_memreq_type          = slice( 2,  6 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )
    s.cs2 = Wire( Bits9 )

    s.stall_M2  = Wire(Bits1) # state signal for if we stalled in M2 stage
    @s.update
    def comb_block_M2(): # comb logic block and setting output ports
                 #  dsize_en|rdata_mux|ostall|memreq_type|memreq|cacheresp
      s.cs2 = concat(   y   , b1(0) ,  n   ,   READ    ,    n ,     n   ) # default
      if s.state_M2.out.val:                                  #  dsize_en|rdata_mux|ostall|memreq_type|memreq|cacheresp
        if s.state_M2.out.is_write_hit_clean:      s.cs2 = concat(   y   ,  b1(0)  ,  n   ,   READ    ,    n ,     n   )
        elif ~s.memreq_rdy or ~s.cacheresp_rdy:    s.cs2 = concat(   n   ,  b1(0)  ,  y   ,   READ    ,    n ,     n   )
        elif s.is_evict_M2.out:                    s.cs2 = concat(   n   ,  b1(0)  ,  n   ,   WRITE   ,    y ,     n   )
        elif s.state_M2.out.is_refill:
          if s.status.cachereq_type_M2 == READ:    s.cs2 = concat(   y   ,  b1(1) ,  n   ,   READ    ,    n ,     y   )
          elif s.status.cachereq_type_M2 == WRITE: s.cs2 = concat(   n   ,  b1(1) ,  n   ,   READ    ,    n ,     n   )
        else:
          if s.status.cachereq_type_M2 == INIT:    s.cs2 = concat(   n   ,  b1(0) ,  n   ,   READ    ,    n ,     y   )
          elif s.status.cachereq_type_M2 == READ:
            if    s.ctrl.hit_M2[0]:                s.cs2 = concat(   y   ,  b1(0) ,  n   ,   READ    ,    n ,     y   )
            elif ~s.ctrl.hit_M2[0]:                s.cs2 = concat(   n   ,  b1(0) ,  n   ,   READ    ,    y ,     n   )
          elif s.status.cachereq_type_M2 == WRITE:
            if s.state_M2.out.is_write_refill:     s.cs2 = concat(   n   ,  b1(0) ,  n   ,   WRITE   ,    n ,     y   )
            elif  s.ctrl.hit_M2[0]:                s.cs2 = concat(   n   ,  b1(0) ,  n   ,   READ    ,    n ,     y   )
            elif ~s.ctrl.hit_M2[0]:                s.cs2 = concat(   n   ,  b1(0) ,  n   ,   READ    ,    y ,     n   )

      s.ctrl.data_size_mux_en_M2  = s.cs2[ CS_data_size_mux_en_M2  ]
      s.ctrl.read_data_mux_sel_M2 = s.cs2[ CS_read_data_mux_sel_M2 ]
      s.ostall_M2                 = s.cs2[ CS_ostall_M2            ]
      s.ctrl.memreq_type          = s.cs2[ CS_memreq_type          ]
      s.cacheresp_en              = s.cs2[ CS_cacheresp_en         ]
      s.memreq_en                 = s.cs2[ CS_memreq_en            ]
      s.stall_M2  = s.ostall_M2
      s.ctrl.reg_en_M2 = ~s.stall_M2

    @s.update
    def stall_logic_M2():
      s.ctrl.stall_mux_sel_M2 = s.was_stalled.out
      s.ctrl.stall_reg_en_M2 = ~s.was_stalled.out

  def line_trace( s ):
    types = ["rd","wr","in"]
    msg_M0 = "  "
    if s.state_M0.val:
      if s.state_M0.is_refill and s.cachereq_rdy:
        msg_M0 = "rf"
      elif s.state_M0.is_refill and not s.cachereq_rdy:
        msg_M0 = "#r"
      elif s.state_M0.is_write_hit_clean and s.cachereq_rdy:
        msg_M0 = "wc"
      elif s.state_M0.is_write_hit_clean and not s.cachereq_rdy:
        msg_M0 = "#w"
      else:
        if s.state_M0.is_write_refill:
          msg_M0 = "wf"
        elif s.state_M0.val:
          msg_M0 = types[s.status.cachereq_type_M0]
    elif not s.cachereq_rdy:
      msg_M0 = "# "

    msg_M1 = "  "
    if s.state_M1.out.val:
      if s.state_M1.out.is_refill:
        msg_M1 = "rf"
      elif s.state_M1.out.is_write_hit_clean:
        msg_M1 = "wc"
      elif s.state_M1.out.is_write_refill:
        msg_M1 = "wf"
      elif ~s.status.hit_M1 and s.status.cachereq_type_M1 != 2:
        msg_M1 = Back.BLACK + Fore.RED + types[s.status.cachereq_type_M1] + Style.RESET_ALL
      elif s.status.hit_M1 and s.status.cachereq_type_M1 != 2:
        msg_M1 = Back.BLACK + Fore.GREEN + types[s.status.cachereq_type_M1] + Style.RESET_ALL
      else:
        msg_M1 = types[s.status.cachereq_type_M1]

    msg_M2 = "  "
    if s.state_M2.out.val:
      if s.state_M2.out.is_refill:            msg_M2 = "rf"
      elif s.state_M2.out.is_write_hit_clean: msg_M2 = "wc"
      elif s.state_M2.out.is_write_refill:    msg_M2 = "wf"
      elif s.is_evict_M2.out:                 msg_M2 = "ev"
      else:                         msg_M2 = types[s.status.cachereq_type_M2]

    msg_memresp = ">" if s.memresp_en else " "
    msg_memreq = ">" if s.memreq_en else " "

    stage1 = "{}|{}".format(msg_memresp,msg_M0) if s.memresp_en \
      else "  {}".format(msg_M0)
    stage2 = "|{}".format(msg_M1)
    stage3 = "|{}{}".format(msg_M2,msg_memreq)
    pipeline = stage1 + stage2 + stage3
    add_msgs = ""
    # add_msgs = f"req_en:{s.cachereq_en} resp_en:{s.cacheresp_en} h:{s.ctrl.hit_M2[0]}"
    return pipeline + add_msgs

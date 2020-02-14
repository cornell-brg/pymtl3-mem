"""
=========================================================================
 BlockingCacheCtrlRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Control
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from .ReplacementPolicy import ReplacementPolicy
from colorama import Fore, Back, Style 
from pymtl3      import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from pymtl3.stdlib.rtl.arithmetics import LeftLogicalShifter
from pymtl3.stdlib.rtl.registers import RegEnRst, RegRst
from mem_pclib.constants.constants   import *

class BlockingCacheCtrlRTL ( Component ):

  def construct( s, param ):

    wdmx0 = param.BitsRdWordMuxSel(0)
    btmx0 = param.BitsRdByteMuxSel(0)
    bbmx0 = param.BitsRd2ByteMuxSel(0)
    acmx0 = Bits2(0) # access select 0
    wben0 = param.BitsDataWben(0)
    wbenf = param.BitsDataWben(-1)
    tg_wbenf = param.BitsTagwben(-1)
    READ  = param.BitsType(MemMsgType.READ)
    WRITE = param.BitsType(MemMsgType.WRITE)
    INIT  = param.BitsType(MemMsgType.WRITE_INIT)

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

    s.cachereq_type_M0      = InPort (param.BitsType)
    s.memresp_type_M0       = InPort (param.BitsType)
    s.MSHR_type             = InPort (param.BitsType)

    s.memresp_mux_sel_M0    = OutPort(Bits1)
    s.addr_mux_sel_M0       = OutPort(Bits2)
    s.wdata_mux_sel_M0      = OutPort(Bits2)
    s.tag_array_val_M0      = OutPort(param.BitsAssoc)
    s.tag_array_type_M0     = OutPort(Bits1)
    s.tag_array_wben_M0     = OutPort(param.BitsTagwben)
    s.ctrl_bit_val_wr_M0    = OutPort(Bits1)
    s.ctrl_bit_dty_wr_M0    = OutPort(Bits1)
    s.reg_en_M0             = OutPort(Bits1)
    
    s.ctrl_bit_rep_wr_M0    = OutPort(param.BitsAssoclog2)
    if param.associativity == 1: # Drive these ports with 0's
      s.ctrl_bit_rep_wr_M0 //= param.BitsAssoclog2(0)

    #--------------------------------------------------------------------------
    # M1 Ctrl Signals
    #--------------------------------------------------------------------------

    s.cachereq_type_M1      = InPort(param.BitsType)
    s.ctrl_bit_dty_rd_M1    = InPort(param.BitsAssoc)
    s.tag_match_M1          = InPort(Bits1) # tag match
    s.offset_M1             = InPort(param.BitsOffset) 
    s.len_M1                = InPort(param.BitsLen)

    s.reg_en_M1             = OutPort(Bits1)
    s.data_array_val_M1     = OutPort(Bits1) 
    s.data_array_type_M1    = OutPort(Bits1)
    s.data_array_wben_M1    = OutPort(param.BitsDataWben)
    s.reg_en_MSHR           = OutPort(Bits1)
    s.evict_mux_sel_M1      = OutPort(Bits1)

    s.stall_mux_sel_M1      = OutPort(Bits1)
    s.stall_reg_en_M1       = OutPort(Bits1)

    # if associativity > 1:
    s.ctrl_bit_rep_rd_M1    = InPort(param.BitsAssoclog2)
    s.ctrl_bit_rep_en_M1    = OutPort(Bits1)
    s.tag_match_way_M1      = InPort(param.BitsAssoclog2) # tag match in which of the ways (asso)
    s.way_offset_M1         = OutPort(param.BitsAssoclog2)
    if param.associativity == 1:
      s.ctrl_bit_rep_en_M1 //= n
      s.way_offset_M1      //= param.BitsAssoclog2(0)

    #---------------------------------------------------------------------------
    # M2 Ctrl Signals
    #--------------------------------------------------------------------------

    s.cachereq_type_M2          = InPort (param.BitsType)
    s.offset_M2                 = InPort (param.BitsOffset)
    s.len_M2                    = InPort (param.BitsLen)
    s.reg_en_M2                 = OutPort(Bits1)
    s.read_data_mux_sel_M2      = OutPort(Bits1) 
    s.read_word_mux_sel_M2      = OutPort(param.BitsRdWordMuxSel)
    s.read_byte_mux_sel_M2      = OutPort(param.BitsRdByteMuxSel)
    s.read_2byte_mux_sel_M2     = OutPort(param.BitsRd2ByteMuxSel)
    s.subword_access_mux_sel_M2 = OutPort(Bits2)
    s.stall_reg_en_M2           = OutPort(Bits1)
    s.stall_mux_sel_M2          = OutPort(Bits1)
    s.hit_M2                    = OutPort(Bits2)
    s.memreq_type               = OutPort(param.BitsType)

    #--------------------------------------------------------------------------
    # Connection Wires
    #--------------------------------------------------------------------------

    s.state_M0 = Wire(param.CtrlMsg)
    s.state_M1 = Wire(param.CtrlMsg)
    s.state_M2 = Wire(param.CtrlMsg)
    s.hit_M1   = Wire(Bits1)

    #--------------------------------------------------------------------------
    # Stall and Ostall Signals
    #--------------------------------------------------------------------------

    s.stall_M0  = Wire(Bits1)
    s.stall_M1  = Wire(Bits1)
    s.stall_M2  = Wire(Bits1)
    s.ostall_M0 = Wire(Bits1)
    s.ostall_M1 = Wire(Bits1)
    s.ostall_M2 = Wire(Bits1)
    s.is_stall  = Wire(Bits1)

    #---------------------------------------------------------------------------
    # Cache-wide FSM
    #--------------------------------------------------------------------------

    # FSM to control refill and evict tranaction conditions. 
    s.curr_state  = Wire(Bits3)
    s.next_state  = Wire(Bits3)
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
      s.next_state = s.curr_state
      if s.curr_state == STATE_GO:
        if s.state_M1.val and not s.state_M1.is_refill and s.cachereq_type_M1 \
          != INIT:
         if s.is_evict_M1:                     s.next_state = STATE_EVICT 
         elif ~s.hit_M1:                       s.next_state = STATE_REFILL 
      elif s.curr_state == STATE_REFILL:
        if s.state_M0.is_refill and s.memresp_type_M0 != WRITE:
          if s.MSHR_type == WRITE:             s.next_state = STATE_REFILL_WRITE
          else:                                s.next_state = STATE_GO
        else:                                  s.next_state = STATE_REFILL
      elif s.curr_state == STATE_EVICT:        
        if not s.is_stall:                     s.next_state = STATE_REFILL
      elif s.curr_state == STATE_REFILL_WRITE: s.next_state = STATE_GO

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

    s.is_refill_reg_M0 = RegRst(Bits1)\
    ( # NO STALLS should occur while refilling
      in_ = s.memresp_en,
      out = s.state_M0.is_refill
    )
    
    if param.associativity > 1: # MSHR for replacement ptr
      # This eases adaptability for nonblocking since we can
      # Store the replacement ptr in the MSHR along all other info
      s.MSHR_ptr_M0 = Wire(param.BitsAssoclog2)
      s.MSHR_rep_ptr_reg_M0 = RegEnRst(param.BitsAssoclog2)(
        en  = s.reg_en_MSHR,
        in_ = s.ctrl_bit_rep_rd_M1,
        out = s.MSHR_ptr_M0,
      )

    @s.update
    def cachereq_logic():
      s.cachereq_rdy = ~s.stall_M1 and s.curr_state == STATE_GO \
                                   and s.next_state != STATE_REFILL \
                                   and s.next_state != STATE_EVICT \
                                   and s.curr_state != STATE_REFILL_WRITE

      if s.state_M1.val and s.cachereq_type_M1 == WRITE and \
        s.state_M0.is_write_hit_clean:
        s.cachereq_rdy = s.cachereq_rdy and n

    @s.update
    def is_write_refill():
      if s.curr_state == STATE_REFILL_WRITE:
        s.state_M0.is_write_refill = y
      else:
        s.state_M0.is_write_refill = n

    CS_tag_array_wben_M0  = slice( 8, 8 + param.bitwidth_tag_wben )
    CS_wdata_mux_sel_M0   = slice( 6, 8 )
    CS_addr_mux_sel_M0    = slice( 4, 6 )
    CS_memresp_mux_sel_M0 = slice( 3, 4 )
    CS_tag_array_type_M0  = slice( 2, 3 )
    CS_ctrl_bit_dty_wr_M0 = slice( 1, 2 )
    CS_ctrl_bit_val_wr_M0 = slice( 0, 1 )

    s.cs0 = Wire( mk_bits( 9 + param.bitwidth_tag_wben ) ) # Bits for control signal table
    @s.update
    def comb_block_M0(): # logic block for setting output ports
      s.state_M0.val = s.cachereq_en or (s.state_M0.is_refill and \
        s.memresp_type_M0 != WRITE) or s.state_M0.is_write_refill or\
           s.state_M0.is_write_hit_clean
      s.ostall_M0 = b1(0)  # Not sure if neccessary but include for completeness
      s.stall_M0  = s.ostall_M0 or s.ostall_M1 or s.ostall_M2
      s.reg_en_M0 = s.memresp_en and ~s.stall_M0

      #               tag_wben|wdat_mux|addr_mux|memrp_mux|tg_ty|dty|val
      s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  ,    x    ,  rd , x , x )
      if s.state_M0.val: #                                          tag_wben|wdat_mux|addr_mux|memrp_mux|tg_ty|dty|val
        if s.state_M0.is_refill:              s.cs0 = concat( tg_wbenf, b2(1)  , b2(1)  , b1(1)   ,  wr , n , y )
        elif s.state_M0.is_write_refill:      s.cs0 = concat( tg_wbenf, b2(2)  , b2(1)  , b1(1)   ,  wr , y , y )
        elif s.state_M0.is_write_hit_clean:   s.cs0 = concat( tg_wbenf, b2(0)  , b2(2)  , b1(0)   ,  wr , y , y )
        else:
          if (s.cachereq_type_M0 == INIT):    s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  , b1(0)   ,  wr , n , y )
          elif (s.cachereq_type_M0 == READ):  s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  , b1(0)   ,  rd , n , n )
          elif (s.cachereq_type_M0 == WRITE): s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  , b1(0)   ,  rd , n , n )

      s.tag_array_type_M0      = s.cs0[ CS_tag_array_type_M0  ]
      s.tag_array_wben_M0      = s.cs0[ CS_tag_array_wben_M0  ]
      s.wdata_mux_sel_M0       = s.cs0[ CS_wdata_mux_sel_M0   ]
      s.memresp_mux_sel_M0     = s.cs0[ CS_memresp_mux_sel_M0 ]
      s.addr_mux_sel_M0        = s.cs0[ CS_addr_mux_sel_M0    ]
      s.ctrl_bit_dty_wr_M0     = s.cs0[ CS_ctrl_bit_dty_wr_M0 ]
      s.ctrl_bit_val_wr_M0     = s.cs0[ CS_ctrl_bit_val_wr_M0 ]
    
    s.way_ptr_M1 = Wire(param.BitsAssoclog2)

    if param.associativity == 1: #val for dmapped cache is simpler
      @s.update
      def Dmapped_tag_array_val_logic_M0():
        if s.state_M0.val:
          s.tag_array_val_M0 = y
        else:
          s.tag_array_val_M0 = n
    else:
      # Tag array valid logic for set asso
      s.rep_ptr_reg_M1 = RegEnRst(param.BitsAssoclog2)(
        en  = s.reg_en_M1,
        in_ = s.MSHR_ptr_M0,
        out = s.way_ptr_M1,
      )
      @s.update
      def Asso_tag_array_val_logic_M0():
        for i in range( param.associativity ):
          s.tag_array_val_M0[i] = n # Enable all SRAMs since we are reading
        if s.state_M0.val:
          if s.state_M0.is_refill:
            s.tag_array_val_M0[s.way_ptr_M1] = y
          elif s.state_M0.is_write_refill:     
            s.tag_array_val_M0[s.way_ptr_M1] = y      
          elif s.cachereq_type_M0 == INIT:
            s.tag_array_val_M0[s.ctrl_bit_rep_rd_M1] = y
          elif s.state_M0.is_write_hit_clean:   
            s.tag_array_val_M0[s.tag_match_way_M1] = y
          else:
            for i in range( param.associativity ):
              if s.cachereq_type_M0 == READ or s.cachereq_type_M0 == WRITE: 
                s.tag_array_val_M0[i] = y # Enable all SRAMs since we are reading
              else:
                s.tag_array_val_M0[i] = n
              
    #--------------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------------
    
    s.ctrl_state_reg_M1 = RegEnRst(param.CtrlMsg)\
    (
      en  = s.reg_en_M1,
      in_ = s.state_M0,
      out = s.state_M1,
    )
    
    s.is_stall_reg_M1 = RegRst(Bits1)(
      in_ = s.stall_M2,
      out = s.is_stall
    )

    @s.update
    def stall_logic_M1():
      s.stall_mux_sel_M1 = s.is_stall
      s.stall_reg_en_M1  = not s.is_stall

    if param.associativity > 1:
      # EXTRA Logic for accounting for set associative caches
      s.repreq_en_M1      = Wire(Bits1)
      s.repreq_rdy_M1     = Wire(Bits1)
      s.repreq_is_hit_M1  = Wire(Bits1)
      s.repreq_hit_ptr_M1 = Wire(param.BitsAssoclog2)
      s.represp_ptr_M1    = Wire(param.BitsAssoclog2)

      s.replacement_M1 = ReplacementPolicy(
        param.BitsAssoc, param.BitsAssoclog2, param.associativity, 0
      )(
        repreq_en       = s.repreq_en_M1,
        repreq_rdy      = s.repreq_rdy_M1,
        repreq_hit_ptr  = s.repreq_hit_ptr_M1,
        repreq_is_hit   = s.repreq_is_hit_M1,
        repreq_ptr      = s.ctrl_bit_rep_rd_M1, # Read replacement mask
        represp_ptr     = s.represp_ptr_M1  # Write new mask
      )
      s.ctrl_bit_rep_wr_M0 //= s.represp_ptr_M1

      @s.update
      def Asso_replacement_logic_M1(): #logic for replacement policy module
        s.repreq_is_hit_M1  = n
        s.repreq_en_M1      = n 
        s.repreq_hit_ptr_M1 = x
        s.ctrl_bit_rep_en_M1 = n
        if s.state_M1.val:
          if s.cachereq_type_M1 == INIT:
            s.repreq_en_M1      = y
            s.repreq_is_hit_M1  = n
          elif not s.is_evict_M1 and not s.state_M1.is_refill and not\
            s.state_M1.is_write_hit_clean and not s.state_M1.is_write_refill:
            # Better to update replacement bit right away
            # because we need it for nonblocking capability
            # For blocking, we can also update during a refill
            # for misses
            if s.hit_M1: 
              s.repreq_hit_ptr_M1 = s.tag_match_way_M1
              s.repreq_en_M1      = y
              s.repreq_is_hit_M1  = y
            else:
              s.repreq_en_M1      = y
              s.repreq_is_hit_M1  = n
        if not s.stall_M1:
          s.ctrl_bit_rep_en_M1 = s.repreq_en_M1

      @s.update
      def Asso_data_array_offset_way_M1():
        s.way_offset_M1 = s.tag_match_way_M1
        if s.state_M1.val:
          if s.state_M1.is_refill or s.state_M1.is_write_refill: 
            s.way_offset_M1 = s.way_ptr_M1
          elif s.hit_M1 or s.cachereq_type_M1 == INIT:
            s.way_offset_M1 = s.tag_match_way_M1
          elif s.is_evict_M1:
            s.way_offset_M1 = s.ctrl_bit_rep_rd_M1

    # Logic for hit detection is same for both
    @s.update
    def hit_logic_M1():
      s.hit_M1 = n
      if s.state_M1.is_write_refill or (s.tag_match_M1 and s.cachereq_type_M1 != INIT):
        # for some reason we also made hit refill a hit 
        # but not actually
        s.hit_M1 = y

      if s.state_M1.is_write_hit_clean:
        s.hit_M1 = s.hit_M1 or y
      s.hit_M2[1]= b1(0)

    # Calculating shift amount
    # 0 -> 0x000f, 1 -> 0x00f0, 2 -> 0x0f00, 3 -> 0xf000
    s.wben_out = Wire(param.BitsDataWben)
    s.wben_in  = Wire(param.BitsDataWben)
    s.WbenGen = LeftLogicalShifter( param.BitsDataWben, clog2(param.bitwidth_data_wben) )(
      in_ = s.wben_in,
      shamt = s.offset_M1,
      out = s.wben_out
    )

    @s.update
    def mask_select_M1():
      if s.len_M1 == 0:
        s.wben_in = param.BitsDataWben(data_array_word_mask)
      elif s.len_M1 == 1:
        s.wben_in = param.BitsDataWben(data_array_byte_mask)
      elif s.len_M1 == 2:
        s.wben_in = param.BitsDataWben(data_array_half_word_mask)
      else:
        s.wben_in = param.BitsDataWben(data_array_word_mask)

    @s.update
    def en_MSHR_M1(): # TEMPORARY; NOT SURE WHAT TO DO WITH THAT SIGNAL YET
      if s.state_M1.val and not s.hit_M1 and not s.curr_state == STATE_REFILL and not s.is_evict_M1\
        and not s.state_M1.is_refill:
        s.reg_en_MSHR = y
      else:
        s.reg_en_MSHR = n

    s.is_dty_M1 = Wire(Bits1)
    if param.associativity == 1:
      s.is_dty_M1 //= s.ctrl_bit_dty_rd_M1
    else: # Multiway set assoc
      @s.update
      def Asso_set_dty_bit_M1():
        if s.hit_M1: 
          s.is_dty_M1 = s.ctrl_bit_dty_rd_M1[s.tag_match_way_M1]
        else:
          s.is_dty_M1 = s.ctrl_bit_dty_rd_M1[s.ctrl_bit_rep_rd_M1]

    @s.update
    def is_write_hit_clean_M0_logic():
      if s.cachereq_type_M1 == WRITE and s.hit_M1 and not s.is_dty_M1 and \
          not s.state_M1.is_write_hit_clean and not s.state_M1.is_write_refill:
        s.state_M0.is_write_hit_clean = y
      else:
        s.state_M0.is_write_hit_clean = n

    @s.update
    def need_evict_M1():
      if s.state_M1.val and not s.state_M1.is_write_refill and \
        not s.hit_M1 and s.is_dty_M1:
        s.is_evict_M1 = y
      else:
        s.is_evict_M1 = n

    @s.update
    def en_M1():
      s.reg_en_M1 = not s.stall_M1 and not s.is_evict_M1

    CS_data_array_wben_M1   = slice( 4,  4 + param.bitwidth_data_wben )
    CS_data_array_type_M1   = slice( 3,  4 )
    CS_data_array_val_M1    = slice( 2,  3 )
    CS_ostall_M1            = slice( 1,  2 )
    CS_evict_mux_sel_M1     = slice( 0,  1 )

    s.cs1 = Wire( mk_bits( 4 + param.bitwidth_data_wben ) )

    @s.update
    def comb_block_M1():
      
      wben = s.wben_out
      s.cs1 = concat(wben0, x , n , n    , b1(0))
      if s.state_M1.val: #                                                wben| ty|val|ostall|addr mux  
        if s.state_M1.is_refill:                    s.cs1 = concat(wbenf, wr, y , n    , b1(0))
        elif s.is_evict_M1:                         s.cs1 = concat(wben0, rd, y , y    , b1(1))
        elif s.state_M1.is_write_hit_clean:         s.cs1 = concat(wbenf, x , n , n    , b1(0))
        else:
          if s.cachereq_type_M1 == INIT:            s.cs1 = concat( wben, wr, y , n    , b1(0))
          elif ~s.hit_M1 and ~s.is_dty_M1:          s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif ~s.hit_M1 and  s.is_dty_M1:          s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif  s.hit_M1 and ~s.is_dty_M1:
            if   s.cachereq_type_M1 == READ:        s.cs1 = concat(wben0, rd, y , n    , b1(0))
            elif s.cachereq_type_M1 == WRITE:       s.cs1 = concat( wben, wr, y , n    , b1(0))
            else:                                   s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif  s.hit_M1 and  s.is_dty_M1:
            if   s.cachereq_type_M1 == READ:        s.cs1 = concat(wben0, rd, y , n    , b1(0))
            elif s.cachereq_type_M1 == WRITE:       s.cs1 = concat( wben, wr, y , n    , b1(0))
      
      s.data_array_type_M1        = s.cs1[ CS_data_array_type_M1 ]
      s.data_array_val_M1         = s.cs1[ CS_data_array_val_M1  ]
      s.data_array_wben_M1        = s.cs1[ CS_data_array_wben_M1 ]
      s.ostall_M1                 = s.cs1[ CS_ostall_M1          ]
      s.evict_mux_sel_M1          = s.cs1[ CS_evict_mux_sel_M1   ]
      s.stall_M1 = s.ostall_M1 or s.ostall_M2

    #--------------------------------------------------------------------------
    # M2 Stage
    #--------------------------------------------------------------------------
    s.is_evict_M2 = Wire(Bits1)

    s.ctrl_state_reg_M2 = RegEnRst(param.CtrlMsg)\
    (
      en  = s.reg_en_M2,
      in_ = s.state_M1,
      out = s.state_M2,
    )

    s.is_evict_reg_M2 = RegEnRst(Bits1)\
    (
      en  = s.reg_en_M2,
      in_ = s.is_evict_M1,
      out = s.is_evict_M2,
    )

    s.hit_reg_M2 = RegEnRst(Bits1)\
    (
      en  = s.reg_en_M2,
      in_ = s.hit_M1,
      out = s.hit_M2[0],
    )

    @s.update
    def en_M2():
      s.reg_en_M2 = ~s.stall_M2

    CS_read_word_mux_sel_M2 = slice( 8,  8 + param.bitwidth_rd_wd_mux_sel )
    CS_read_data_mux_sel_M2 = slice( 7,  8 )
    CS_ostall_M2            = slice( 6,  7 )
    CS_memreq_type          = slice( 2,  6 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )
    s.cs2 = Wire( mk_bits( 8 + param.bitwidth_rd_wd_mux_sel ) )
    s.msel = Wire(param.BitsRdWordMuxSel)

    @s.update
    def comb_block_M2(): # comb logic block and setting output ports
      s.msel = param.BitsRdWordMuxSel(s.offset_M2[2:param.bitwidth_offset]) + param.BitsRdWordMuxSel(1)  
      s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     n   ) # default
      if s.state_M2.val:                                     #  word_mux|rdata_mux|ostall|memreq_type|memreq|cacheresp
        if ~s.memreq_rdy or ~s.cacheresp_rdy:s.cs2 = concat(wdmx0,   b1(0) ,  y   ,   READ    ,    n ,     n   )
        elif s.is_evict_M2:                  s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   WRITE   ,    y ,     n   )
        elif s.state_M2.is_refill:
          if s.cachereq_type_M2 == READ:     s.cs2 = concat(s.msel,  b1(1) ,  n   ,   READ    ,    n ,     y   )
          elif s.cachereq_type_M2 == WRITE:  s.cs2 = concat(wdmx0,   b1(1) ,  n   ,   READ    ,    n ,     y   )
        elif s.state_M2.is_write_hit_clean:  s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     n   )
        else:
          if s.cachereq_type_M2 == INIT:     s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     y   )
          elif s.cachereq_type_M2 == READ:
            if    s.hit_M2[0]:               s.cs2 = concat(s.msel,  b1(0) ,  n   ,   READ    ,    n ,     y   )
            elif ~s.hit_M2[0]:               s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    y ,     n   )
          elif s.cachereq_type_M2 == WRITE:
            if s.state_M2.is_write_refill:   s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     n   )
            elif  s.hit_M2[0]:               s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     y   )
            elif ~s.hit_M2[0]:               s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    y ,     n   )

      s.memreq_en                 = s.cs2[ CS_memreq_en            ]
      s.cacheresp_en              = s.cs2[ CS_cacheresp_en         ]
      s.read_word_mux_sel_M2      = s.cs2[ CS_read_word_mux_sel_M2 ]
      s.read_data_mux_sel_M2      = s.cs2[ CS_read_data_mux_sel_M2 ]
      s.memreq_type               = s.cs2[ CS_memreq_type          ]
      s.ostall_M2                 = s.cs2[ CS_ostall_M2            ]
      s.stall_M2  = s.ostall_M2

    @s.update
    def subword_access_mux_sel_logic_M2():
      s.read_byte_mux_sel_M2  = btmx0
      s.read_2byte_mux_sel_M2 = bbmx0
      s.subword_access_mux_sel_M2 = acmx0
      if s.cachereq_type_M2 == READ:
        if s.hit_M2[0] or s.state_M2.is_refill:
          s.subword_access_mux_sel_M2 = s.len_M2
          if s.len_M2 == 1:
            s.read_byte_mux_sel_M2 = s.offset_M2[0:2]
          elif s.len_M2 == 2:
            s.read_2byte_mux_sel_M2 = s.offset_M2[1:2]

    @s.update
    def stall_logic_M2():
      s.stall_mux_sel_M2 = s.is_stall
      s.stall_reg_en_M2 = not s.is_stall

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
          msg_M0 = types[s.cachereq_type_M0]
    elif not s.cachereq_rdy:
      msg_M0 = "# "

    msg_M1 = "  "
    if s.state_M1.val:
      if s.state_M1.is_refill:
        msg_M1 = "rf"
      elif s.state_M1.is_write_hit_clean:
        msg_M1 = "wc"
      elif ~s.hit_M1 and s.cachereq_type_M1 != 2:
        msg_M1 = Fore.RED + types[s.cachereq_type_M1] + Style.RESET_ALL
      elif s.state_M1.is_write_refill:
        msg_M1 = "wf"
      elif s.hit_M1 and s.cachereq_type_M1 != 2:
        msg_M1 = Fore.GREEN + types[s.cachereq_type_M1] + Style.RESET_ALL
      else:
        msg_M1 = types[s.cachereq_type_M1]

    msg_M2 = "  "
    if s.state_M2.val:
      if s.state_M2.is_refill:            msg_M2 = "rf"
      elif s.state_M2.is_write_hit_clean: msg_M2 = "wc"
      elif s.state_M2.is_write_refill:    msg_M2 = "wf"
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
    add_msgs = ""
    return pipeline + add_msgs 

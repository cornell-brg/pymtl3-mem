"""
=========================================================================
 BlockingCacheCtrlRTL.py
=========================================================================
Parameterizable Pipelined Blocking Cache Control
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from .ReplacementPolicy              import ReplacementPolicy
from colorama                        import Fore, Back, Style
from mem_pclib.constants.constants   import *
from pymtl3                          import *
from pymtl3.stdlib.ifcs.MemMsg       import MemMsgType
from pymtl3.stdlib.rtl.arithmetics   import LeftLogicalShifter
from pymtl3.stdlib.rtl.registers     import RegEnRst, RegRst

class BlockingCacheCtrlRTL ( Component ):

  def construct( s, p ):

    # TEMP NAMES: Will come up with something
    wdmx0 = p.BitsRdWordMuxSel(0)
    btmx0 = p.BitsRdByteMuxSel(0)
    bbmx0 = p.BitsRd2ByteMuxSel(0)
    acmx0 = Bits2(0) # access select 0
    wben0 = p.BitsDataWben(0)
    wbenf = p.BitsDataWben(-1)
    tg_wbenf = p.BitsTagwben(-1)
    READ  = p.BitsType(MemMsgType.READ)
    WRITE = p.BitsType(MemMsgType.WRITE)
    INIT  = p.BitsType(MemMsgType.WRITE_INIT)

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

    s.dpath_in      = InPort(p.DpathSignalsOut)
    s.ctrl_out      = OutPort(p.CtrlSignalsOut)

    #--------------------------------------------------------------------------
    # Stall and Ostall Signals
    #--------------------------------------------------------------------------

    s.stall_M0  = Wire(Bits1)
    s.stall_M1  = Wire(Bits1)
    s.stall_M2  = Wire(Bits1)
    s.ostall_M0 = Wire(Bits1)
    s.ostall_M1 = Wire(Bits1)
    s.ostall_M2 = Wire(Bits1)

    #--------------------------------------------------------------------------
    # Y Stage
    #--------------------------------------------------------------------------

    @s.update
    def mem_resp_rdy():
      # TODO Update for Non-blocking capability
      s.memresp_rdy = y # Always yes for blocking cache

    #--------------------------------------------------------------------------
    # M0 Stage
    #---------------------------------------------------------------------------

    s.memresp_en_M0 = Wire(Bits1)
    s.is_refill_reg_M0 = RegEnRst(Bits1)\
    ( # NO STALLS should occur while refilling
      en  = s.ctrl_out.reg_en_M0,
      in_ = s.memresp_en,
      out = s.memresp_en_M0
    )
    s.MSHR_replay_next_M0 = Wire(Bits1)
    s.MSHR_replay_now_M0 = Wire(Bits1)
    s.MSHR_replay_reg_M0 = RegEnRst(Bits1)(
      en  = s.ctrl_out.reg_en_M0,
      in_ = s.MSHR_replay_next_M0,
      out = s.MSHR_replay_now_M0
    )

    s.state_M0 = Wire(p.CtrlMsg)
    @s.update
    def ctrl_logic_M0():
      s.state_M0.is_refill = n
      s.state_M0.is_write_refill = n
      s.ctrl_out.MSHR_dealloc_en = n
      s.MSHR_replay_next_M0 = n
      if s.memresp_en_M0 and s.dpath_in.memresp_type_M0 != WRITE:
        s.state_M0.is_refill = y
        if s.dpath_in.MSHR_type == READ:
          s.ctrl_out.MSHR_dealloc_en = y
        # Replay logic  
        if not s.dpath_in.MSHR_empty:
          s.MSHR_replay_next_M0 = y
      elif s.MSHR_replay_now_M0:
        if not s.dpath_in.MSHR_empty:
          if s.dpath_in.MSHR_type == WRITE:
            s.state_M0.is_write_refill = y
            s.ctrl_out.MSHR_dealloc_en = y
          elif s.dpath_in.MSHR_type == READ:
            s.state_M0.is_refill = y
          s.MSHR_replay_next_M0 = y

    s.state_M1 = Wire(p.CtrlMsg)
    @s.update
    def cachereq_logic():
      s.cachereq_rdy = y
      if (s.state_M1.val and s.dpath_in.cachereq_type_M1 == WRITE and \
        s.state_M0.is_write_hit_clean) \
          or s.stall_M0 \
          or s.dpath_in.MSHR_full or not s.dpath_in.MSHR_empty:
        s.cachereq_rdy = n

    CS_tag_array_wben_M0  = slice( 7, 7 + p.bitwidth_tag_wben )
    CS_wdata_mux_sel_M0   = slice( 6, 7 )
    CS_addr_mux_sel_M0    = slice( 4, 6 )
    CS_memresp_mux_sel_M0 = slice( 3, 4 )
    CS_tag_array_type_M0  = slice( 2, 3 )
    CS_ctrl_bit_dty_wr_M0 = slice( 1, 2 )
    CS_ctrl_bit_val_wr_M0 = slice( 0, 1 )

    s.cs0 = Wire( mk_bits( 9 + p.bitwidth_tag_wben ) ) # Bits for control signal table
    @s.update
    def comb_block_M0(): # logic block for setting output ports
      s.state_M0.val = s.cachereq_en or (s.state_M0.is_refill and \
        s.dpath_in.memresp_type_M0 != WRITE) or s.state_M0.is_write_refill or\
           s.state_M0.is_write_hit_clean
      s.ostall_M0 = b1(0)  # Not sure if neccessary but include for completeness
      s.stall_M0  = s.ostall_M0 or s.ostall_M1 or s.ostall_M2
      s.ctrl_out.reg_en_M0 = ~s.stall_M0

      #               tag_wben|wdat_mux|addr_mux|memrp_mux|tg_ty|dty|val
      s.cs0 = concat( tg_wbenf, b2(0)  , b2(0)  ,    x    ,  rd , x , x )
      if s.state_M0.val: #                                    tag_wben|wdat_mux|addr_mux|memrp_mux|tg_ty|dty|val
        if s.state_M0.is_refill:              s.cs0 = concat( tg_wbenf, b1(1)  , b2(1)  , b1(1)   ,  wr , n , y )
        elif s.state_M0.is_write_refill:      s.cs0 = concat( tg_wbenf, b1(0)  , b2(1)  , b1(1)   ,  wr , y , y )
        elif s.state_M0.is_write_hit_clean:   s.cs0 = concat( tg_wbenf, b1(0)  , b2(2)  , b1(0)   ,  wr , y , y )
        else:
          if (s.dpath_in.cachereq_type_M0 == INIT):    s.cs0 = concat( tg_wbenf, b1(0)  , b2(0)  , b1(0)   ,  wr , n , y )
          elif (s.dpath_in.cachereq_type_M0 == READ):  s.cs0 = concat( tg_wbenf, b1(0)  , b2(0)  , b1(0)   ,  rd , n , n )
          elif (s.dpath_in.cachereq_type_M0 == WRITE): s.cs0 = concat( tg_wbenf, b1(0)  , b2(0)  , b1(0)   ,  rd , n , n )

      s.ctrl_out.tag_array_wben_M0      = s.cs0[ CS_tag_array_wben_M0  ]
      s.ctrl_out.wdata_mux_sel_M0       = s.cs0[ CS_wdata_mux_sel_M0   ]
      s.ctrl_out.memresp_mux_sel_M0     = s.cs0[ CS_memresp_mux_sel_M0 ]
      s.ctrl_out.addr_mux_sel_M0        = s.cs0[ CS_addr_mux_sel_M0    ]
      s.ctrl_out.tag_array_type_M0      = s.cs0[ CS_tag_array_type_M0  ]
      s.ctrl_out.ctrl_bit_dty_wr_M0     = s.cs0[ CS_ctrl_bit_dty_wr_M0 ]
      s.ctrl_out.ctrl_bit_val_wr_M0     = s.cs0[ CS_ctrl_bit_val_wr_M0 ]

    s.way_ptr_M1 = Wire(p.BitsAssoclog2)
    s.rep_ptr_reg_M1 = RegEnRst(p.BitsAssoclog2)(
      en  = s.ctrl_out.reg_en_M1,
      in_ = s.dpath_in.MSHR_ptr,
      out = s.way_ptr_M1,
    )
    @s.update
    def tag_array_val_logic_M0():
      # Most of the logic is for associativity > 1; should simplify for dmapped
      for i in range( p.associativity ):
        s.ctrl_out.tag_array_val_M0[i] = n # Enable all SRAMs since we are reading
      if s.state_M0.val:
        if s.state_M0.is_refill:
          s.ctrl_out.tag_array_val_M0[s.way_ptr_M1] = y
        elif s.state_M0.is_write_refill:     
          s.ctrl_out.tag_array_val_M0[s.way_ptr_M1] = y      
        elif s.dpath_in.cachereq_type_M0 == INIT:
          s.ctrl_out.tag_array_val_M0[s.dpath_in.ctrl_bit_rep_rd_M1] = y
        elif s.state_M0.is_write_hit_clean:   
          s.ctrl_out.tag_array_val_M0[s.dpath_in.tag_match_way_M1] = y
        else:
          for i in range( p.associativity ):
            if s.dpath_in.cachereq_type_M0 == READ or s.dpath_in.cachereq_type_M0 == WRITE: 
              s.ctrl_out.tag_array_val_M0[i] = y # Enable all SRAMs since we are reading
            else:
              s.ctrl_out.tag_array_val_M0[i] = n
              
    #--------------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------------

    s.ctrl_state_reg_M1 = RegEnRst(p.CtrlMsg)\
    (
      en  = s.ctrl_out.reg_en_M1,
      in_ = s.state_M0,
      out = s.state_M1,
    )
    
    s.is_stall_M1 = RegRst(Bits1)(
      in_ = s.stall_M2,
    )

    @s.update
    def stall_logic_M1():
      s.ctrl_out.stall_mux_sel_M1 = s.is_stall_M1.out
      s.ctrl_out.stall_reg_en_M1  = not s.is_stall_M1.out

    s.is_evict_M1 = Wire(Bits1)
    s.hit_M1   = Wire(Bits1)

    if p.associativity > 1:
      # EXTRA Logic for accounting for set associative caches
      s.repreq_en_M1      = Wire(Bits1)
      s.repreq_rdy_M1     = Wire(Bits1)
      s.repreq_is_hit_M1  = Wire(Bits1)
      s.repreq_hit_ptr_M1 = Wire(p.BitsAssoclog2)
      s.represp_ptr_M1    = Wire(p.BitsAssoclog2)

      s.replacement_M1 = ReplacementPolicy(
        p.BitsAssoc, p.BitsAssoclog2, p.associativity, 0
      )(
        repreq_en       = s.repreq_en_M1,
        repreq_rdy      = s.repreq_rdy_M1,
        repreq_hit_ptr  = s.repreq_hit_ptr_M1,
        repreq_is_hit   = s.repreq_is_hit_M1,
        repreq_ptr      = s.dpath_in.ctrl_bit_rep_rd_M1, # Read replacement mask
        represp_ptr     = s.represp_ptr_M1  # Write new mask
      )
      s.ctrl_out.ctrl_bit_rep_wr_M0 //= s.represp_ptr_M1

      @s.update
      def Asso_replacement_logic_M1(): #logic for replacement policy module
        s.repreq_is_hit_M1  = n
        s.repreq_en_M1      = n
        s.repreq_hit_ptr_M1 = x
        s.ctrl_out.ctrl_bit_rep_en_M1 = n
        if s.state_M1.val:
          if s.dpath_in.cachereq_type_M1 == INIT:
            s.repreq_en_M1      = y
            s.repreq_is_hit_M1  = n
          elif not s.is_evict_M1 and not s.state_M1.is_refill and not\
            s.state_M1.is_write_hit_clean and not s.state_M1.is_write_refill:
            # Better to update replacement bit right away
            # because we need it for nonblocking capability
            # For blocking, we can also update during a refill
            # for misses
            if s.hit_M1:
              s.repreq_hit_ptr_M1 = s.dpath_in.tag_match_way_M1
              s.repreq_en_M1      = y
              s.repreq_is_hit_M1  = y
            else:
              s.repreq_en_M1      = y
              s.repreq_is_hit_M1  = n
        if not s.stall_M1:
          s.ctrl_out.ctrl_bit_rep_en_M1 = s.repreq_en_M1

      @s.update
      def Asso_data_array_offset_way_M1():
        s.ctrl_out.way_offset_M1 = s.dpath_in.tag_match_way_M1
        if s.state_M1.val:
          if s.state_M1.is_refill or s.state_M1.is_write_refill:
            s.ctrl_out.way_offset_M1 = s.way_ptr_M1
          elif s.hit_M1 or s.dpath_in.cachereq_type_M1 == INIT:
            s.ctrl_out.way_offset_M1 = s.dpath_in.tag_match_way_M1
          elif s.is_evict_M1:
            s.ctrl_out.way_offset_M1 = s.dpath_in.ctrl_bit_rep_rd_M1
    else:
      s.ctrl_out.ctrl_bit_rep_wr_M0 //= p.BitsAssoclog2(0)
      s.ctrl_out.ctrl_bit_rep_en_M1 //= n
      s.ctrl_out.way_offset_M1      //= p.BitsAssoclog2(0)

    # Logic for hit detection is same for both
    @s.update
    def hit_logic_M1():
      s.hit_M1 = n
      if s.state_M1.is_write_refill or (s.dpath_in.tag_match_M1 and s.dpath_in.cachereq_type_M1 != INIT):
        # for some reason we also made hit refill a hit
        # but not actually
        s.hit_M1 = y

      if s.state_M1.is_write_hit_clean:
        s.hit_M1 = s.hit_M1 or y
      s.ctrl_out.hit_M2[1]= b1(0)

    # Calculating shift amount
    # 0 -> 0x000f, 1 -> 0x00f0, 2 -> 0x0f00, 3 -> 0xf000
    s.wben_in  = Wire(p.BitsDataWben)
    s.WbenGen = LeftLogicalShifter( p.BitsDataWben, clog2(p.bitwidth_data_wben) )(
      in_ = s.wben_in,
      shamt = s.dpath_in.offset_M1,
    )

    @s.update
    def mask_select_M1():
      if s.dpath_in.len_M1 == 0:
        s.wben_in = p.BitsDataWben(data_array_word_mask)
      elif s.dpath_in.len_M1 == 1:
        s.wben_in = p.BitsDataWben(data_array_byte_mask)
      elif s.dpath_in.len_M1 == 2:
        s.wben_in = p.BitsDataWben(data_array_half_word_mask)
      else:
        s.wben_in = p.BitsDataWben(data_array_word_mask)

    @s.update
    def en_MSHR_M1(): # TEMPORARY; NOT SURE WHAT TO DO WITH THAT SIGNAL YET
      if s.state_M1.val and not s.hit_M1 and not s.is_evict_M1\
        and not s.state_M1.is_refill and s.dpath_in.cachereq_type_M1!= INIT\
          and not s.stall_M1:
        s.ctrl_out.MSHR_alloc_en = y
      else:
        s.ctrl_out.MSHR_alloc_en = n

    s.is_dty_M1 = Wire(Bits1)
    @s.update
    def Asso_set_dty_bit_M1():
      if s.hit_M1: 
        s.is_dty_M1 = s.dpath_in.ctrl_bit_dty_rd_M1[s.dpath_in.tag_match_way_M1]
      else:
        s.is_dty_M1 = s.dpath_in.ctrl_bit_dty_rd_M1[s.dpath_in.ctrl_bit_rep_rd_M1]

    @s.update
    def is_write_hit_clean_M0_logic():
      if s.dpath_in.cachereq_type_M1 == WRITE and s.hit_M1 and not s.is_dty_M1 and \
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
      s.ctrl_out.reg_en_M1 = not s.stall_M1 and not s.is_evict_M1

    CS_data_array_wben_M1   = slice( 4,  4 + p.bitwidth_data_wben )
    CS_data_array_type_M1   = slice( 3,  4 )
    CS_data_array_val_M1    = slice( 2,  3 )
    CS_ostall_M1            = slice( 1,  2 )
    CS_evict_mux_sel_M1     = slice( 0,  1 )

    s.cs1 = Wire( mk_bits( 4 + p.bitwidth_data_wben ) )

    @s.update
    def comb_block_M1():
      wben = s.WbenGen.out
      s.cs1 = concat(wben0, x , n , n    , b1(0))
      if s.state_M1.val: #                                                wben| ty|val|ostall|addr mux  
        if s.state_M1.is_refill:                       s.cs1 = concat(wbenf, wr, y , n    , b1(0))
        elif s.is_evict_M1:                            s.cs1 = concat(wben0, rd, y , y    , b1(1))
        elif s.state_M1.is_write_hit_clean:            s.cs1 = concat(wbenf, x , n , n    , b1(0))
        else:
          if s.dpath_in.cachereq_type_M1 == INIT:      s.cs1 = concat( wben, wr, y , n    , b1(0))
          elif ~s.hit_M1 and ~s.is_dty_M1:             s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif ~s.hit_M1 and  s.is_dty_M1:             s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif  s.hit_M1 and ~s.is_dty_M1:
            if   s.dpath_in.cachereq_type_M1 == READ:  s.cs1 = concat(wben0, rd, y , n    , b1(0))
            elif s.dpath_in.cachereq_type_M1 == WRITE: s.cs1 = concat( wben, wr, y , n    , b1(0))
            else:                                      s.cs1 = concat(wben0, x , n , n    , b1(0))
          elif  s.hit_M1 and  s.is_dty_M1:
            if   s.dpath_in.cachereq_type_M1 == READ:  s.cs1 = concat(wben0, rd, y , n    , b1(0))
            elif s.dpath_in.cachereq_type_M1 == WRITE: s.cs1 = concat( wben, wr, y , n    , b1(0))
      
      s.ctrl_out.data_array_type_M1        = s.cs1[ CS_data_array_type_M1 ]
      s.ctrl_out.data_array_val_M1         = s.cs1[ CS_data_array_val_M1  ]
      s.ctrl_out.data_array_wben_M1        = s.cs1[ CS_data_array_wben_M1 ]
      s.ostall_M1                          = s.cs1[ CS_ostall_M1          ]
      s.ctrl_out.evict_mux_sel_M1          = s.cs1[ CS_evict_mux_sel_M1   ]
      s.stall_M1 = s.ostall_M1 or s.ostall_M2

    #--------------------------------------------------------------------------
    # M2 Stage
    #--------------------------------------------------------------------------
    
    s.state_M2 = RegEnRst(p.CtrlMsg)\
    (
      en  = s.ctrl_out.reg_en_M2,
      in_ = s.state_M1,
    )

    s.is_evict_M2 = RegEnRst(Bits1)\
    (
      en  = s.ctrl_out.reg_en_M2,
      in_ = s.is_evict_M1,
    )

    s.hit_reg_M2 = RegEnRst(Bits1)\
    (
      en  = s.ctrl_out.reg_en_M2,
      in_ = s.hit_M1,
      out = s.ctrl_out.hit_M2[0],
    )

    @s.update
    def en_M2():
      s.ctrl_out.reg_en_M2 = ~s.stall_M2

    CS_read_word_mux_sel_M2 = slice( 8,  8 + p.bitwidth_rd_wd_mux_sel )
    CS_read_data_mux_sel_M2 = slice( 7,  8 )
    CS_ostall_M2            = slice( 6,  7 )
    CS_memreq_type          = slice( 2,  6 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )
    s.cs2 = Wire( mk_bits( 8 + p.bitwidth_rd_wd_mux_sel ) )
    s.msel = Wire(p.BitsRdWordMuxSel)

    @s.update
    def comb_block_M2(): # comb logic block and setting output ports
      s.msel = p.BitsRdWordMuxSel(s.dpath_in.offset_M2[2:p.bitwidth_offset]) + p.BitsRdWordMuxSel(1)
      s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     n   ) # default
      if s.state_M2.out.val:                                     #  word_mux|rdata_mux|ostall|s.ctrl_out.memreq_type|memreq|cacheresp
        if ~s.memreq_rdy or ~s.cacheresp_rdy:         s.cs2 = concat(wdmx0,   b1(0) ,  y   ,   READ    ,    n ,     n   )
        elif s.is_evict_M2.out:                       s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   WRITE   ,    y ,     n   )
        elif s.state_M2.out.is_refill:
          if s.dpath_in.cachereq_type_M2 == READ:     s.cs2 = concat(s.msel,  b1(1) ,  n   ,   READ    ,    n ,     y   )
          elif s.dpath_in.cachereq_type_M2 == WRITE:  s.cs2 = concat(wdmx0,   b1(1) ,  n   ,   READ    ,    n ,     y   )
        elif s.state_M2.out.is_write_hit_clean:       s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     n   )
        else:
          if s.dpath_in.cachereq_type_M2 == INIT:     s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     y   )
          elif s.dpath_in.cachereq_type_M2 == READ:
            if    s.ctrl_out.hit_M2[0]:               s.cs2 = concat(s.msel,  b1(0) ,  n   ,   READ    ,    n ,     y   )
            elif ~s.ctrl_out.hit_M2[0]:               s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    y ,     n   )
          elif s.dpath_in.cachereq_type_M2 == WRITE:
            if s.state_M2.out.is_write_refill:        s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     n   )
            elif  s.ctrl_out.hit_M2[0]:               s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    n ,     y   )
            elif ~s.ctrl_out.hit_M2[0]:               s.cs2 = concat(wdmx0,   b1(0) ,  n   ,   READ    ,    y ,     n   )

      s.memreq_en                          = s.cs2[ CS_memreq_en            ]
      s.cacheresp_en                       = s.cs2[ CS_cacheresp_en         ]
      s.ctrl_out.read_word_mux_sel_M2      = s.cs2[ CS_read_word_mux_sel_M2 ]
      s.ctrl_out.read_data_mux_sel_M2      = s.cs2[ CS_read_data_mux_sel_M2 ]
      s.ctrl_out.memreq_type               = s.cs2[ CS_memreq_type          ]
      s.ostall_M2                          = s.cs2[ CS_ostall_M2            ]
      s.stall_M2  = s.ostall_M2

    @s.update
    def subword_access_mux_sel_logic_M2():
      # TODO Put in its own module
      s.ctrl_out.read_byte_mux_sel_M2  = btmx0
      s.ctrl_out.read_2byte_mux_sel_M2 = bbmx0
      s.ctrl_out.subword_access_mux_sel_M2 = acmx0
      if s.dpath_in.cachereq_type_M2 == READ:
        if s.ctrl_out.hit_M2[0] or s.state_M2.out.is_refill:
          # s.ctrl_out.subword_access_mux_sel_M2 = s.dpath_in.len_M2
          if s.dpath_in.len_M2 == 1:
            s.ctrl_out.read_byte_mux_sel_M2 = s.dpath_in.offset_M2[0:2]
            s.ctrl_out.subword_access_mux_sel_M2 = Bits2(1)
          elif s.dpath_in.len_M2 == 2:
            s.ctrl_out.read_2byte_mux_sel_M2 = s.dpath_in.offset_M2[1:2]
            s.ctrl_out.subword_access_mux_sel_M2 = Bits2(2)

    @s.update
    def stall_logic_M2():
      s.ctrl_out.stall_mux_sel_M2 = s.is_stall_M1.out
      s.ctrl_out.stall_reg_en_M2 = ~s.is_stall_M1.out

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
          msg_M0 = types[s.dpath_in.cachereq_type_M0]
    elif not s.cachereq_rdy:
      msg_M0 = "# "

    msg_M1 = "  "
    if s.state_M1.val:
      if s.state_M1.is_refill:
        msg_M1 = "rf"
      elif s.state_M1.is_write_hit_clean:
        msg_M1 = "wc"
      elif ~s.hit_M1 and s.dpath_in.cachereq_type_M1 != 2:
        msg_M1 = Fore.RED + types[s.dpath_in.cachereq_type_M1] + Style.RESET_ALL
      elif s.state_M1.is_write_refill:
        msg_M1 = "wf"
      elif s.hit_M1 and s.dpath_in.cachereq_type_M1 != 2:
        msg_M1 = Fore.GREEN + types[s.dpath_in.cachereq_type_M1] + Style.RESET_ALL
      else:
        msg_M1 = types[s.dpath_in.cachereq_type_M1]

    msg_M2 = "  "
    if s.state_M2.out.val:
      if s.state_M2.out.is_refill:            msg_M2 = "rf"
      elif s.state_M2.out.is_write_hit_clean: msg_M2 = "wc"
      elif s.state_M2.out.is_write_refill:    msg_M2 = "wf"
      elif s.is_evict_M2.out:                 msg_M2 = "ev"
      else:                         msg_M2 = types[s.dpath_in.cachereq_type_M2]

    msg_memresp = ">" if s.memresp_en else " "
    msg_memreq = ">" if s.memreq_en else " "

    states = ["Go","Rf","Ev","Wf","Wr"]
    stage1 = "{}|{}".format(msg_memresp,msg_M0) if s.memresp_en \
      else "  {}".format(msg_M0)
    stage2 = "|{}".format(msg_M1)
    stage3 = "|{}{}".format(msg_M2,msg_memreq)
    pipeline = stage1 + stage2 + stage3
    add_msgs = ""
    add_msgs += f" rf:{s.state_M0.is_refill} wf:{s.state_M0.is_write_refill}"
    add_msgs += f" al:{s.ctrl_out.MSHR_alloc_en} de:{s.ctrl_out.MSHR_dealloc_en} | emp:{s.dpath_in.MSHR_empty}"
    add_msgs += f" full:{s.dpath_in.MSHR_full} rep:{s.MSHR_replay_now_M0}"
    return pipeline + add_msgs

#=========================================================================
# BlockingCacheCtrlPRTL.py
#=========================================================================

from pymtl3      import *
from pymtl3.stdlib.rtl.registers import RegEnRst, RegRst
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from pymtl3.stdlib.rtl.arithmetics import LShifter

STATE_GO     = b2(0)
STATE_REFILL = b2(1)
STATE_EVICT  = b2(2)

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
    # Constants
    wr = y = b1(1)
    rd = n = b1(0)
    READ  = MemMsgType.READ
    WRITE = MemMsgType.WRITE
    INIT  = MemMsgType.WRITE_INIT
    mxsel0 = BitsRdDataMux(0)
    wben0 = BitsDataWben(0)
    wbenf = BitsDataWben(-1)
    data_array_wb_mask = 2**(dbw//8)-1
    

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
    
    s.cachereq_type_M0    = InPort(BitsType)
    s.memresp_mux_sel_M0  = OutPort(Bits1)
    s.tag_array_val_M0    = OutPort(Bits1)
    s.tag_array_type_M0   = OutPort(Bits1)
    s.tag_array_wben_M0   = OutPort(BitsTagWben) 
    s.ctrl_bit_val_wr_M0  = OutPort(Bits1)
    s.reg_en_M0           = OutPort(Bits1)
    
    #-------------------------------------------------------------------
    # M1 Ctrl Signals
    #-------------------------------------------------------------------
    
    s.cachereq_type_M1   = InPort(BitsType)
    s.ctrl_bit_val_rd_M1 = InPort(Bits1)
    # s.ctrl_bit_dty_rd_M1 = InPort(Bits1)
    s.tag_match_M1       = InPort(Bits1)
    s.offset_M1          = InPort(BitsOffset)
    
    # s.ctrl_bit_dty_wr_M1 = OutPort(Bits1)
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
    s.curr_state = Wire(Bits2)
    s.next_state = Wire(Bits2)
    s.state_transition_block = RegRst(Bits2, STATE_GO)(
      out = s.curr_state,
      in_ = s.next_state
    )
    @s.update
    def next_state_block():
      if s.curr_state == STATE_GO:
        # if ~s.hit_M1: #and s.ctrl_bit_dty_rd_M0:     
          # s.next_state = STATE_EVICT
        if s.val_M1 and s.cachereq_type_M1 != INIT and ~s.hit_M1 and ~s.is_refill_M1: #and ~ s.ctrl_bit_dty_rd_M0: 
          s.next_state = STATE_REFILL
      elif s.curr_state == STATE_REFILL:
        if s.is_refill_M0:                          s.next_state = STATE_GO
        else:                                       s.next_state = STATE_REFILL
      elif s.curr_state == STATE_EVICT:             s.next_state = STATE_REFILL
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
    s.is_refill_reg_M0 = RegRst(Bits1)( #NO STALLS should occur while refilling
      # en  = b1(1),
      in_ = s.memresp_en,
      out = s.is_refill_M0
    )
    # Valid
    s.val_M0 = Wire(Bits1)
    CS_tag_array_wben_M0    = slice( 4,  4 + twb ) # last because variable
    CS_memresp_mux_sel_M0   = slice( 3,  4 )
    CS_tag_array_type_M0    = slice( 2,  3 )
    CS_tag_array_val_M0     = slice( 1,  2 )
    CS_ctrl_bit_val_wr_M0   = slice( 0,  1 )

    s.cs0 = Wire( mk_bits( 5 + twb ) ) # Bits for CS parameterized
    @s.update 
    def en_MSHR(): # TEMPORARY; NOT SURE WHAT TO DO WITH THAT SIGNAL YET
      if not s.hit_M1 and not s.curr_state == STATE_REFILL:
        s.reg_en_MSHR = b1(1)
      else:
        s.reg_en_MSHR = b1(0)

    @s.update
    def stall_logic_M0():
      s.stall_M0 = s.ostall_M0 or s.ostall_M1 or s.ostall_M2    # Check stall for all stages
      s.ostall_M0 = b1(0)  # Not sure if neccessary but include for completeness
      s.cachereq_rdy = (~s.stall_M1 and s.curr_state == STATE_GO) and s.next_state != STATE_REFILL # No more request if we are stalling
      
    @s.update
    def comb_block_M0(): # logic block for setting output ports
      s.val_M0 = s.cachereq_en or s.is_refill_M0
      s.reg_en_M0 = s.memresp_en
      if s.val_M0:#                                          tag_wben         |mr_mux|tg_ty|tg_v|val
        if s.is_refill_M0:                   s.cs0 = concat( BitsTagWben(0xf), b1(1),   wr,   y, y)    
        else:
          if (s.cachereq_type_M0 == INIT):   s.cs0 = concat( BitsTagWben(0xf), b1(0),   wr,   y, y)
          elif (s.cachereq_type_M0 == READ): s.cs0 = concat( BitsTagWben(0x0), b1(0),   rd,   y, n)
          elif (s.cachereq_type_M0 == WRITE):s.cs0 = concat( BitsTagWben(0x0), b1(0),   rd,   y, n)
          else:                              s.cs0 = concat( BitsTagWben(0x0), b1(0),   rd,   n, n)
      else:                                  s.cs0 = concat( BitsTagWben(0x0), b1(0),   rd,   n, n)

      s.tag_array_type_M0  = s.cs0[ CS_tag_array_type_M0  ]
      s.tag_array_val_M0   = s.cs0[ CS_tag_array_val_M0   ]
      s.tag_array_wben_M0  = s.cs0[ CS_tag_array_wben_M0  ]
      s.ctrl_bit_val_wr_M0 = s.cs0[ CS_ctrl_bit_val_wr_M0 ]
      s.memresp_mux_sel_M0 = s.cs0[ CS_memresp_mux_sel_M0 ]

    #--------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------
    s.val_M1 = Wire(Bits1)
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

    CS_data_array_wben_M1   = slice( 2,  2 + dwb )
    CS_data_array_type_M1   = slice( 1,  2 )
    CS_data_array_val_M1    = slice( 0,  1 )
    s.cs1 = Wire( mk_bits( 2 + dwb ) )
    @s.update
    def hit_logic_M1():
      s.hit_M1 = (s.tag_match_M1 and s.ctrl_bit_val_rd_M1 \
        and s.cachereq_type_M1 != INIT) #MemMsgType.WRITE_INIT)
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
    def en_M1():
      s.reg_en_M1 = ~s.stall_M1

    @s.update
    def comb_block_M1(): 
      s.wben_in = BitsDataWben(data_array_wb_mask)
      wben = s.wben_out
      if s.val_M1: #                                          wben| ty|val
        if s.is_refill_M1:                    s.cs1 = concat(wbenf, wr, y )
        else:      
          if s.cachereq_type_M1 == INIT:      s.cs1 = concat( wben, wr, y )
          elif s.hit_M1 == y:
            if s.cachereq_type_M1 == READ:    s.cs1 = concat(wben0, rd, y )
            elif s.cachereq_type_M1 == WRITE: s.cs1 = concat( wben, wr, y )
            else:                             s.cs1 = concat(wben0, n, n )
          else:                               s.cs1 = concat(wben0, n, n )
      else:                                   s.cs1 = concat(wben0, n, n )
      s.data_array_type_M1        = s.cs1[ CS_data_array_type_M1 ]
      s.data_array_val_M1         = s.cs1[ CS_data_array_val_M1  ]
      s.data_array_wben_M1        = s.cs1[ CS_data_array_wben_M1 ]      


    @s.update
    def stall_logic_M1():
      s.stall_M1 = b1(0)
      s.ostall_M1 = b1(0)
      # if not s.hit_M1 and s.val_M1:
      #   s.ostall_M1 = b1(1)
      # else:
      #   s.ostall_M1 = b1(0)
    #-----------------------------------------------------
    # M2 Stage 
    #-----------------------------------------------------
    s.val_M2 = Wire(Bits1)

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

    CS_read_word_mux_sel_M2 = slice( 3,  3 + rmx2 )
    CS_read_data_mux_sel_M2 = slice( 2,  3 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )
    s.cs2 = Wire( mk_bits( 3 + rmx2 ) )

    s.msel = Wire(BitsRdDataMux)
    @s.update
    def comb_block_M2(): # comb logic block and setting output ports
      s.msel = BitsRdDataMux(s.offset_M2) + BitsRdDataMux(1)  
      s.reg_en_M2 = ~s.stall_M2
      if s.val_M2:                                     #  word_mux|rdata_mux|memreq|cacheresp  
        if s.is_refill_M2:                   s.cs2 = concat(s.msel,   b1(1) ,    n ,     y   )
        else:
          if (s.cachereq_type_M2 == INIT):   s.cs2 = concat(mxsel0,   b1(0) ,    n ,     y   )
          elif (s.cachereq_type_M2 == READ):
            if s.hit_M2[0]:                  s.cs2 = concat(s.msel,   b1(0) ,    n ,     y   )
            else:                            s.cs2 = concat(mxsel0,   b1(0) ,    y ,     n   )
          elif (s.cachereq_type_M2 == WRITE):s.cs2 = concat(mxsel0,   b1(0) ,    n ,     y   )
          else:                              s.cs2 = concat(mxsel0,   b1(0) ,    n ,     n   )
      else:                                  s.cs2 = concat(mxsel0,   b1(0) ,    n ,     n   )
        
      s.memreq_en                 = s.cs2[ CS_memreq_en            ]
      s.cacheresp_en              = s.cs2[ CS_cacheresp_en         ] 
      s.read_word_mux_sel_M2      = s.cs2[ CS_read_word_mux_sel_M2 ]
      s.read_data_mux_sel_M2      = s.cs2[ CS_read_data_mux_sel_M2 ]

    @s.update
    def stall_logic_M2():
      s.ostall_M2 = ~s.memreq_rdy or ~s.cacheresp_rdy

  def line_trace( s ):
    types = ["rd","wr","in"]
    if s.is_refill_M0 and s.val_M0: msg_M0 = "rf" 
    else:
      if s.val_M0:
        msg_M0 = types[s.cachereq_type_M0]  
      elif s.cachereq_en:
        msg_M0 = "# "
      else: 
        msg_M0 = "  "
    msg_M1 = "rf" if s.is_refill_M1 and s.val_M1 else types[s.cachereq_type_M1] if s.val_M1 else "  "
    msg_M2 = "rf" if s.is_refill_M2 and s.val_M2 else types[s.cachereq_type_M2] if s.val_M2 else "  "
    msg_memresp = ">" if s.memresp_en else " "
    msg_memreq = ">" if s.memreq_en else " "    

    states = ["G","R"]
    msg_state = states[s.curr_state]  
    stage1 = "{}|{}".format(msg_memresp,msg_M0) if s.curr_state == STATE_REFILL and \
      s.memresp_en else "  {}".format(msg_M0)
    stage2 = "|{}".format(msg_M1)
    stage3 = "|{}{}".format(msg_M2,msg_memreq)
    state    = " [{}] ".format(msg_state)
    pipeline = stage1 + stage2 + stage3 + state
    # additional_msg = "CRqrdy:{} MRqprdy:{}".format(\
    #   s.cachereq_rdy,s.memreq_rdy)
    additional_msg = "H1:{}".format(s.hit_M1)

    return pipeline + additional_msg

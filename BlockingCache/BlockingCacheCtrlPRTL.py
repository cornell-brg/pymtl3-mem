#=========================================================================
# BlockingCacheCtrlPRTL.py
#=========================================================================

from pymtl3      import *
from pymtl3.stdlib.rtl.registers import RegEnRst
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

class BlockingCacheCtrlPRTL ( Component ):
  def construct( s,
                 dbw   = 32,       # offset bitwidth
                 ofw   = 4,       # offset bitwidth
                 BitsAddr = "inv",    # address bitstruct
                 BitsOpaque    = "inv",    # opaque 
                 BitsType    = "inv",    # type
                 BitsData    = "inv",    # data 
                 BitsCacheline    = "inv",    # cacheline 
                 BitsIdx    = "inv",    # index 
                 BitsTag    = "inv",    # tag 
                 BitsOffset    = "inv",    # offset 
                 BitsTagWben   = "inv",    # Tag array write byte enable
                 BitsDataWben   = "inv",    # Data array write byte enable
                 BitsRdDataMux   = "inv",    # Read data mux M2 
                 twb = 4,        # Tag array write byte enable bitwidth
                 dwb = 16,       # Data array write byte enable bitwidth
                 rmx2 = 3,        # Read word mux bitwidth
  ):
    # Constants
    wr = y = b1(1)
    rd = n = b1(0)
    WRITE = BitsType(1)
    INIT = BitsType(2)
    READ = BitsType(0)
    mxsel0 = BitsRdDataMux(0)
    wben0 = BitsDataWben(0)

    
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
    s.reg_en_M0          = OutPort(Bits1)
    
    #-------------------------------------------------------------------
    # M1 Ctrl Signals
    #-------------------------------------------------------------------
    
    s.cachereq_type_M1   = InPort(BitsType)
    s.ctrl_bit_val_rd_M1 = InPort(Bits1)
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

    #--------------------------------------------------------------------
    # M0 Stage (Refill Request)
    #--------------------------------------------------------------------
    # Stall logic
    # s.stall_M0 = Wire(Bits1)    
    # Valid
    s.val_M0 = Wire(Bits1)
    CS_tag_array_wben_M0    = slice( 6,  6 + twb ) # last because variable
    CS_memresp_mux_sel_M0    = slice( 5,  6 )
    CS_tag_array_type_M0    = slice( 4,  5 )
    CS_tag_array_val_M0     = slice( 3,  4 )
    CS_ctrl_bit_val_wr_M0   = slice( 2,  3 )
    CS_memresp_rdy         = slice( 1,  2 )
    CS_cachereq_rdy        = slice( 0,  1 )
    s.cs0 = Wire( mk_bits( 6 + twb ) )

    @s.update
    def dummy_driver():
      s.reg_en_MSHR = b1(1)
    @s.update
    def comb_block_M0(): # logic block for setting output ports
      s.val_M0 = s.cachereq_en
      s.reg_en_M0 = s.memresp_en
      # s.cachereq_rdy = b1(1)
      # s.memresp_rdy = b1(0)
      if s.val_M0:#                                         tag_wben       |mr_mux|tg_ty|tg_v|val|memresp|cachereq
        if (s.cachereq_type_M0 == INIT):   s.cs0 = concat( BitsTagWben(0xf),b1(0),  wr,   y,    y,    n,      y    )
        elif (s.cachereq_type_M0 == READ): s.cs0 = concat( BitsTagWben(0x0),b1(0),  rd,   y,    n,    n,      y    )
        elif (s.cachereq_type_M0 == WRITE):s.cs0 = concat( BitsTagWben(0x0),b1(0),  rd,   y,    n,    n,      y    )
        else:                              s.cs0 = concat( BitsTagWben(0x0),b1(0),  rd,   n,    n,    n,      y    )
      else:                                s.cs0 = concat( BitsTagWben(0x0),b1(0),  rd,   n,    n,    n,      y    )

      s.tag_array_type_M0  = s.cs0[ CS_tag_array_type_M0  ]
      s.tag_array_val_M0   = s.cs0[ CS_tag_array_val_M0   ]
      s.tag_array_wben_M0  = s.cs0[ CS_tag_array_wben_M0  ]
      s.ctrl_bit_val_wr_M0 = s.cs0[ CS_ctrl_bit_val_wr_M0 ]
      s.memresp_rdy        = s.cs0[ CS_memresp_rdy       ]
      s.cachereq_rdy       = s.cs0[ CS_cachereq_rdy      ]  
      s.memresp_mux_sel_M0 = s.cs0[ CS_memresp_mux_sel_M0 ]
    #--------------------------------------------------------------------
    # M1 Stage
    #--------------------------------------------------------------------
    s.val_M1 = Wire(Bits1)
    s.val_reg_M1 = RegEnRst(Bits1)(
      en  = s.reg_en_M1,
      in_ = s.val_M0,
      out = s.val_M1,
    )
    CS_data_array_wben_M1   = slice( 2,  2 + dwb )
    CS_data_array_type_M1   = slice( 1,  2 )
    CS_data_array_val_M1    = slice( 0,  1 )
    s.cs1 = Wire( mk_bits( 2 + dwb ) )
    s.hit_M1 = Wire(Bits1)
    
    @s.update
    def hit_logic_M1():
      s.hit_M1 = (s.tag_match_M1 and s.ctrl_bit_val_rd_M1 \
        and s.cachereq_type_M1 != INIT)#MemMsgType.WRITE_INIT)
      s.hit_M2[1]= b1(0)
    
    # 0 -> 0x000f, 1 -> 0x00f0, 2 -> 0x0f00, 3 -> 0xf000 
    s.shift_amt = Wire(mk_bits(clog2(dwb)))
    s.shift_amt[2:ofw] //= s.offset_M1
    s.shift_amt[0:2] //= b2(0)
    @s.update
    def comb_block_M1(): 
      wben = BitsDataWben(2**(dbw//8)-1) << s.shift_amt  
      print ("wben: "+str(wben))
      # wben = s.wben
      s.reg_en_M1 = y
      if s.val_M1: #                                         wben |ty|val      
        if (s.cachereq_type_M1 == INIT):     s.cs1 = concat( wben, wr, y )
        elif s.hit_M1 == y:
          if (s.cachereq_type_M1 == READ):   s.cs1 = concat( wben0,rd, y )
          elif (s.cachereq_type_M1 == WRITE):s.cs1 = concat( wben, wr, y )
          else:                              s.cs1 = concat(wben0, n, n )
        else:                                s.cs1 = concat(wben0, n, n )
      else:                                  s.cs1 = concat(wben0, n, n )
      s.data_array_type_M1        = s.cs1[ CS_data_array_type_M1 ]
      s.data_array_val_M1         = s.cs1[ CS_data_array_val_M1  ]
      s.data_array_wben_M1        = s.cs1[ CS_data_array_wben_M1 ]      

    #-----------------------------------------------------
    # M2 Stage 
    #-----------------------------------------------------
    s.val_M2 = Wire(Bits1)
    s.val_reg_M2 = RegEnRst(Bits1)(
      en  = s.reg_en_M2,
      in_ = s.val_M1,
      out = s.val_M2,
    )
    s.hit_reg_M2 = RegEnRst(Bits1)(
      en  = s.reg_en_M2,
      in_ = s.hit_M1,
      out = s.hit_M2[0],
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
      s.reg_en_M2 = y
      if s.val_M2:                                    #  word_mux|rdata_mux|memreq|cacheresp  
        if (s.cachereq_type_M2 == INIT):   s.cs2 = concat(mxsel0, b1(0),     n,       y   )
        elif (s.cachereq_type_M2 == READ): s.cs2 = concat(s.msel, b1(0),     n,       y   )
        elif (s.cachereq_type_M2 == WRITE):s.cs2 = concat(mxsel0, b1(0),     n,       y   )
        else:                              s.cs2 = concat(mxsel0, b1(0),     n,       n   )
      else:                                s.cs2 = concat(mxsel0, b1(0),     n,       n   )
        
      s.memreq_en                 = s.cs2[ CS_memreq_en            ]
      s.cacheresp_en              = s.cs2[ CS_cacheresp_en         ] 
      s.read_word_mux_sel_M2      = s.cs2[ CS_read_word_mux_sel_M2 ]
      s.read_data_mux_sel_M2      = s.cs2[ CS_read_data_mux_sel_M2 ]


  def line_trace( s ):
    types = ["rd","wr","in"]
    msg_M0 = types[s.cachereq_type_M0]  if s.val_M0 else "  "
    msg_M1 = types[s.cachereq_type_M1] if s.val_M1 else "  "
    msg_M2 = types[s.cachereq_type_M2] if s.val_M2 else "  "
    
    return "|{}|{}|{}|  H_M1:{} H_M2:{} TM_M1:{} mux2:{}".format(\
      msg_M0,msg_M1,msg_M2,s.hit_M1,s.hit_M2,s.tag_match_M1,
      s.read_word_mux_sel_M2) 

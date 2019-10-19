#=========================================================================
# BlockingCacheCtrlPRTL.py
#=========================================================================

from pymtl3      import *
from pymtl3.stdlib.rtl.registers import RegEnRst
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

class BlockingCacheCtrlPRTL ( Component ):
  def construct( s,
                 obw = 8,			      # Opaque bitwidth
                 abw  = 32,
                 dbw  = 32,
                 size = 8192, # Cache size in bytes
                 clw  = 128, # Short name for cacheline bitwidth
                 way  = 1, # associativity
  ):
    #-------------------------------------------------------------------------
    # Bitwidths
    #-------------------------------------------------------------------------
    nbl = size*8//clw       # Number of Cache Blocks
    idw = clog2(nbl)        # Index bitwidth
    ofw = clog2(clw//8)     # Offset bitwidth
    tgw = abw - ofw - idw   # Tag bitwidth

    #-------------------------------------------------------------------------
    # Dtypes
    #-------------------------------------------------------------------------
    ab = mk_bits(abw)
    ob = mk_bits(obw)
    ty = mk_bits(4) # type is always 4 bits
    db = mk_bits(dbw)
    cl = mk_bits(clw)
    ix = mk_bits(idw)
    tg = mk_bits(tgw)
    wb_bits = int(clw+7)//8
    wb_d = mk_bits(wb_bits)
    wr = y  = b1(1)
    rd = n  = b1(0)

    s.cachereq_en   = InPort(Bits1)
    s.cachereq_rdy  = OutPort(Bits1)

    s.cacheresp_en  = OutPort(Bits1)
    s.cacheresp_rdy = InPort(Bits1) 

    s.memreq_en     = OutPort(Bits1)
    s.memreq_rdy    = InPort(Bits1)

    s.memresp_en    = InPort(Bits1)
    s.memresp_rdy   = OutPort(Bits1)
    #-----------------
    # Y  Ctrl Signals 
    #-----------------
    s.cachereq_type_Y      = InPort(ty)
    s.tag_array_val_Y      = OutPort(Bits1)
    s.tag_array_type_Y     = OutPort(Bits1)
    s.tag_array_wben_Y     = OutPort(Bits4) # Data array wb is always 4 bits
    s.ctrl_bit_val_wr_Y    = OutPort(Bits1)
    #-----------------
    # M0 Ctrl Signals 
    #-----------------
    s.reg_en_M0           = OutPort(Bits1)
    #-----------------
    # M1 Ctrl Signals
    #-----------------
    s.cachereq_type_M1      = InPort(ty)
    s.ctrl_bit_val_rd_M1    = InPort(Bits1)
    s.tag_match_M1          = InPort(Bits1)
    s.reg_en_M1             = OutPort(Bits1)
    s.data_array_val_M1     = OutPort(Bits1)
    s.data_array_type_M1    = OutPort(Bits1)
    s.data_array_wben_M1    = OutPort(wb_d)
    #-----------------
    # M2 Ctrl Signals
    #-----------------
    s.cachereq_type_M2      = InPort(ty)
    s.reg_en_M2             = OutPort(Bits1)
    # s.read_data_mux_sel_M2  = OutPort(mk_bits(clog2(2)))
    s.read_word_mux_sel_M2  = OutPort(mk_bits(clog2(5)))
    # Output Signals
    s.hit_M2                = OutPort(Bits2)
    #--------------------------------------------------------------------
    # Y  Stage
    #--------------------------------------------------------------------
    # Stall logic
    # s.stall_M0 = Wire(Bits1)
    
    #Valid
    s.val_Y = Wire(Bits1)
    s.val_Y //= s.cachereq_en
    CS_tag_array_type_Y    = slice( 8,  9 )
    CS_tag_array_val_Y     = slice( 7,  8 )
    CS_tag_array_wben_Y    = slice( 3,  7 )
    CS_ctrl_bit_val_wr_Y   = slice( 2,  3 )
    CS_memresp_rdy         = slice( 1,  2 )
    CS_cachereq_rdy        = slice( 0,  1 )
    s.csY = Wire( Bits32 )
    @s.update
    def comb_block_Y():
      # s.cachereq_rdy = b1(1)
      # s.memresp_rdy = b1(0)
      if s.val_Y:#                                                      tg_ty tg_v  tg_wben  val  memresp cachereq
        if (s.cachereq_type_Y == MemMsgType.WRITE_INIT): s.csY = concat( wr,   y,  b4(0xf),  y,    n,      y    )
        elif (s.cachereq_type_Y == MemMsgType.READ):     s.csY = concat( rd,   y,  b4(0xf),  n,    n,      y    )
        else:                                            s.csY = concat( rd,   n,  b4(0xf),  n,    n,      y    )
      else:                                              s.csY = concat( rd,   n,  b4(0xf),  n,    n,      y    )

    @s.update
    def signal_unpack_M0():
      s.tag_array_type_Y         = s.csY[ CS_tag_array_type_Y       ]
      s.tag_array_val_Y          = s.csY[ CS_tag_array_val_Y        ]
      s.tag_array_wben_Y         = s.csY[ CS_tag_array_wben_Y       ]
      s.ctrl_bit_val_wr_Y        = s.csY[ CS_ctrl_bit_val_wr_Y      ]
      s.memresp_rdy              = s.csY[ CS_memresp_rdy            ]
      s.cachereq_rdy             = s.csY[ CS_cachereq_rdy           ]
    
    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    s.val_M0 = Wire(Bits1)
    s.val_M0 //= s.memresp_rdy 
    s.tem_M0 = Wire(Bits1)
    s.val_reg_M0 = RegEnRst(Bits1)(
      en  = s.reg_en_M0,
      in_ = s.val_M0,
      out = s.tem_M0,
    )
    @s.update
    def comb_block_M0():
      s.reg_en_M0 = n
      
    #-----------------------------------------------------
    # M1 Stage 
    #-----------------------------------------------------
    s.val_M1 = Wire(Bits1)
    s.val_reg_M1 = RegEnRst(Bits1)(
      en  = s.reg_en_M1,
      in_ = s.val_Y,
      out = s.val_M1,
    )
    CS_data_array_wben_M1   = slice( 2,  2 + wb_bits  )
    CS_data_array_type_M1   = slice( 1,  2 )
    CS_data_array_val_M1    = slice( 0,  1 )
    s.cs1 = Wire( Bits32 )
    s.hit_M1 = Wire(Bits1)
    s.hit_reg_M1 = RegEnRst(Bits1)(
      en  = s.reg_en_M1,
      in_ = s.hit_M1,
      out = s.hit_M2[0],
    )
    @s.update
    def hit_logic_M1():
      s.hit_M1 = (s.tag_match_M1 and s.ctrl_bit_val_rd_M1 and s.cachereq_type_M1 != MemMsgType.WRITE_INIT)
      s.hit_M2[1]= b1(0)
    @s.update
    def comb_block_M1():
      s.reg_en_M1 = y
      if s.val_M1: #                                                       wben       ty  val      
        if (s.cachereq_type_M1 == MemMsgType.WRITE_INIT): s.cs1 = concat( wb_d(0xf),  wr,  y,  )
        elif (s.cachereq_type_M1 == MemMsgType.READ):     s.cs1 = concat( wb_d(0),    rd,  y,  )
        else:                                             s.cs1 = concat( wb_d(0),    n,   n,  )
      else:                                               s.cs1 = concat( wb_d(0),    n,   n,  )
          
    @s.update
    def signal_unpack_M1(): 
      s.data_array_type_M1        = s.cs1[ CS_data_array_type_M1      ]
      s.data_array_val_M1         = s.cs1[ CS_data_array_val_M1       ]
      s.data_array_wben_M1        = s.cs1[ CS_data_array_wben_M1      ]

    #-----------------------------------------------------
    # M2 Stage 
    #-----------------------------------------------------
    s.val_M2 = Wire(Bits1)
    s.val_reg_M2 = RegEnRst(Bits1)(
      en  = s.reg_en_M2,
      in_ = s.val_M1,
      out = s.val_M2,
    )
    CS_read_word_mux_sel_M2 = slice( 2,  5 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )
    s.cs2 = Wire( Bits32 )
    
    @s.update
    def comb_block_M2():
      # if s.cacheresp_rdy:
      #   s.cacheresp_en = b1(1)
      # s.memreq_en = b1(0)
      s.reg_en_M2 = y
      if s.val_M2:#                                                      word_mux  memreq  cacheresp  
        if (s.cachereq_type_M2 == MemMsgType.WRITE_INIT): s.cs2 = concat( b3(0),     n,       y,    )
        elif (s.cachereq_type_M2 == MemMsgType.READ):     s.cs2 = concat( b3(1) ,    n,       y,    )
        else:                                             s.cs2 = concat( b3(0),     n,       n,   )
      else:                                               s.cs2 = concat( b3(0),     n,       n,   )
    @s.update
    def signal_unpack_M2():
      s.memreq_en                 = s.cs2[ CS_memreq_en            ]
      s.cacheresp_en              = s.cs2[ CS_cacheresp_en         ]
      s.read_word_mux_sel_M2      = s.cs2[ CS_read_word_mux_sel_M2 ]

    # DUMMY DRIVER
    # Drives signals not used so we stop getting errors about it
    # @s.update
    # def driver():
    #   # s.cachereq_rdy = n
    #   s.cacheresp_en = n
    #   # s.memresp_rdy  = n
    #   s.memreq_en    = n
    #   # s.reg_en_M1    = y 
    #   # s.data_array_val_M1  = y 
    #   # s.data_array_type_M1 = wr
    #   # s.data_array_wben_M1 = b16(0)
    #   # s.hit                  = b2(1)   #M1
    #   s.reg_en_M2          = y
    #   s.read_word_mux_sel_M2 = b3(3)

  def line_trace( s ):
    types = ["rd","wr","in"]
    msg_Y  = types[s.cachereq_type_Y]  if s.val_Y  else "  "
    msg_M0 = types[s.cachereq_type_Y]  if s.val_M0 else "  "
    msg_M1 = types[s.cachereq_type_M1] if s.val_M1 else "  "
    msg_M2 = types[s.cachereq_type_M2] if s.val_M2 else "  "
    
    return "|{}|{}|{}|{}|  H:{}".format(\
      msg_Y,msg_M0,msg_M1,msg_M2,s.hit_M1) 

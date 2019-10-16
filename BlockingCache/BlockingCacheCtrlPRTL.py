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
    w = y  = b1(1)
    r = n  = b1(0)

    s.cachereq_en   = InPort(Bits1)
    s.cachereq_rdy  = OutPort(Bits1)

    s.cacheresp_en  = OutPort(Bits1)
    s.cacheresp_rdy = InPort(Bits1) 

    s.memreq_en     = OutPort(Bits1)
    s.memreq_rdy    = InPort(Bits1)

    s.memresp_en    = InPort(Bits1)
    s.memresp_rdy   = OutPort(Bits1)
    #-----------------
    # M0 Ctrl Signals 
    #-----------------
    s.cachereq_type_M0      = InPort(ty)
    # s.reg_en_M0             = OutPort(Bits1)
    # s.write_data_mux_sel_M0 = OutPort(mk_bits(clog2(2)))
    # tag array
    s.tag_array_val_M0      = OutPort(Bits1)
    s.tag_array_type_M0     = OutPort(Bits1)
    s.tag_array_wben_M0     = OutPort(Bits4) # Data array wb is always 4 bits
    #-----------------
    # M1 Ctrl Signals
    #-----------------
    s.cachereq_type_M1      = InPort(ty)
    s.tag_match_M1          = InPort(Bits1)
    s.reg_en_M1             = OutPort(Bits1)
    # data array
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
    s.hit                   = OutPort(Bits2)
    #--------------------------------------------------------------------
    # M0 Stage
    #--------------------------------------------------------------------
    # Stall logic
    s.stall_M0 = Wire(Bits1)
    
    #Valid
    s.val_M0 = Wire(Bits1)
    s.val_M0 //= s.cachereq_en
    CS_tag_array_type_M0   = slice( 7,  8 )
    CS_tag_array_val_M0    = slice( 6,  7 )
    CS_tag_array_wben_M0   = slice( 3,  6 )
    CS_memresp_rdy         = slice( 1,  2 )
    CS_cachereq_rdy        = slice( 0,  1 )
    s.cs0 = Wire( Bits32 )
    @s.update
    def comb_block_M0():
      # s.cachereq_rdy = b1(1)
      # s.memresp_rdy = b1(0)
      if (s.cachereq_type_M0 == MemMsgType.WRITE_INIT):
        #              ty val wben      memresp cachereq
        s.cs0 = concat( w, y,  b4(0xf),   n,      y    )
      elif (s.cachereq_type_M0 == MemMsgType.READ):
        s.cs0 = concat( r, y,  b4(0xf),   n,      y    )
      else:
        print("INVALID TYPE M0")
        s.cs0 = concat( r, n,  b4(0xf),   n,      y    )

    @s.update
    def signal_unpack_M0():
      s.tag_array_type_M0         = s.cs0[ CS_tag_array_type_M0       ]
      s.tag_array_val_M0          = s.cs0[ CS_tag_array_val_M0        ]
      s.tag_array_wben_M0         = s.cs0[ CS_tag_array_wben_M0       ]
      s.memresp_rdy               = s.cs0[ CS_memresp_rdy             ]
      s.cachereq_rdy              = s.cs0[ CS_cachereq_rdy            ]

    #-----------------------------------------------------
    # M1 Stage 
    #-----------------------------------------------------
    s.val_M1 = Wire(Bits1)
    s.val_reg_M1 = RegEnRst(Bits1)(
      en  = s.reg_en_M1,
      in_ = s.val_M0,
      out = s.val_M1,
    )
    CS_data_array_wben_M1   = slice( 3,  3 + wb_bits  )
    CS_reg_en_M1            = slice( 2,  3 )
    CS_data_array_type_M1   = slice( 1,  2 )
    CS_data_array_val_M1    = slice( 0,  1 )
    s.cs1 = Wire( Bits32 )
    @s.update
    def comb_block_M1():
      if (s.cachereq_type_M1 == MemMsgType.WRITE_INIT):
        #                   wben   en  ty  val      
        s.cs1 = concat( wb_d(0xf), y,  w,  y,   )
      elif (s.cachereq_type_M1 == MemMsgType.READ):
        s.cs1 = concat( wb_d(0),   y,  r,  y,   )
      else:
        print("INVALID TYPE M1")
        s.cs1 = concat( wb_d(0),   y,  n,  n,  )
    s.hit[0:1] //= s.tag_match_M1

    @s.update
    def signal_unpack_M1():
      s.reg_en_M1                 = s.cs1[ CS_reg_en_M1               ]
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
    CS_read_word_mux_sel_M2 = slice( 3,  6 )
    CS_reg_en_M2            = slice( 2,  3 )
    CS_memreq_en            = slice( 1,  2 )
    CS_cacheresp_en         = slice( 0,  1 )
    s.cs2 = Wire( Bits32 )
    @s.update
    def comb_block_M2():
      # if s.cacheresp_rdy:
      #   s.cacheresp_en = b1(1)
      # s.memreq_en = b1(0)
      # s.reg_en_M2 = b1(1)
      if (s.val_M2):
        if (s.cachereq_type_M2 == MemMsgType.WRITE_INIT):
          #              word_mux en  memreq  cacheresp        
          s.cs2 = concat( b3(0),  y,   n,       y,      )
        elif (s.cachereq_type_M2 == MemMsgType.READ):
          s.cs2 = concat( b3(1) , y,   n,       y,         )
        else:
          print("INVALID TYPE M2")
          s.cs2 = concat( b3(0),  y,   n,       n,   )
    @s.update
    def signal_unpack_M2():
      s.reg_en_M2                 = s.cs2[ CS_reg_en_M2            ]
      s.memreq_en                 = s.cs2[ CS_memreq_en            ]
      s.cacheresp_en              = s.cs2[ CS_cacheresp_en         ]
      s.read_word_mux_sel_M2      = s.cs2[ CS_read_word_mux_sel_M2 ]

  def line_trace( s ):
    types = ["rd","wr","in"]
    
    msg_M0 = types[s.cachereq_type_M0] if s.val_M0 else "  "
    msg_M1 = types[s.cachereq_type_M1] if s.val_M1 else "  "
    msg_M2 = types[s.cachereq_type_M2] if s.val_M2 else "  "
    
    return "|{}|{}|{}|  c_rdy{}|ty0{}|ty1{}".format(\
      msg_M0,msg_M1,msg_M2,s.cachereq_rdy,s.cachereq_type_M0,
      s.cachereq_type_M1) 

"""
=========================================================================
CacheDerivedParams.py
=========================================================================
Generates constants and bitstructs from cache parameters

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   10 February 2020
"""

from pymtl3 import *

from .cacheStructs import *

class CacheDerivedParams:
  def __repr__( self ):
    return f"{self.CacheReqType}_{self.CacheRespType}_"\
           f"{self.MemReqType}_{self.MemRespType}_{self.num_bytes}_{self.associativity}"

  def __init__( self, CacheReqType, CacheRespType, MemReqType, MemRespType,
                num_bytes, associativity ):

    self.num_bytes     = num_bytes
    self.CacheReqType  = CacheReqType
    self.CacheRespType = CacheRespType
    self.MemReqType    = MemReqType
    self.MemRespType   = MemRespType
    self.associativity = associativity

    #--------------------------------------------------------------------------
    # Bitwidths
    #--------------------------------------------------------------------------

    assert( MemReqType.get_field_type("data").nbits == MemRespType.get_field_type("data").nbits )
    assert( MemReqType.get_field_type("opaque").nbits == MemRespType.get_field_type("opaque").nbits )

    assert( CacheReqType.get_field_type("data").nbits == CacheRespType.get_field_type("data").nbits )
    assert( CacheReqType.get_field_type("opaque").nbits == CacheRespType.get_field_type("opaque").nbits )

    self.bitwidth_cacheline        = MemReqType.get_field_type("data").nbits
    self.bitwidth_addr             = MemReqType.get_field_type("addr").nbits
    self.bitwidth_opaque           = MemReqType.get_field_type("opaque").nbits
    self.bitwidth_data             = CacheReqType.get_field_type("data").nbits
    # Convert to total number of bits and then divide
    self.total_num_cachelines      = self.num_bytes * 8 // self.bitwidth_cacheline
    self.nblocks_per_way           = self.total_num_cachelines // self.associativity # cachelines per way
    self.bitwidth_num_lines        = clog2( self.total_num_cachelines )
    self.bitwidth_index            = clog2( self.nblocks_per_way )                   # index width
    self.bitwidth_offset           = clog2( self.bitwidth_cacheline // 8 )           # offset bitwidth
    self.bitwidth_tag              = self.bitwidth_addr - self.bitwidth_offset - self.bitwidth_index # tag bitwidth
    self.bitwidth_data_wben        = int( self.bitwidth_cacheline + 7 ) // 8 * 8     # Data array write mask bitwidth
    self.bitwidth_rd_data_mux_sel  = clog2( self.bitwidth_cacheline // self.bitwidth_data + 1 ) # Read data mux bitwidth
    self.bitwidth_rd_byte_mux_sel  = clog2( self.bitwidth_data // 8  )               # Read byte mux sel bitwidth
    self.bitwidth_rd_2byte_mux_sel = clog2( self.bitwidth_data // 16 )               # Read half word mux sel bitwidth
#    self.bitwidth_rd_word_mux_sel  = clog2( bitwidth_rd_word_mux_sel )               # Read word mux bitwidth
    self.bitwidth_len              = clog2( self.bitwidth_data // 8  )
    if self.associativity == 1:
      self.bitwidth_clog_asso      = 1
    else:
      self.bitwidth_clog_asso      = clog2( self.associativity )
    self.bitwidth_mem_len          = clog2( self.bitwidth_cacheline // 8 )

    self.bitwidth_dirty            = self.bitwidth_cacheline // 32  # 1 dirty bit per 32-bit word
    self.bitwidth_val              = 1                              # Valid bit

    # sum of the tag bitwidth, valid, and dirty bit per word and rounded
    # up to multiple of 8
    self.bitwidth_tag_array        = int( self.bitwidth_tag + self.bitwidth_val + self.bitwidth_dirty + 7 ) // 8 * 8
    self.bitwidth_tag_wben         = self.bitwidth_tag_array # Tag array write byte bitwidth
    self.bitwidth_tag_remainder    = self.bitwidth_tag_array - self.bitwidth_tag - self.bitwidth_dirty - self.bitwidth_val

    # print( "size[{}], asso[{}], clw[{}], tag[{}], idx[{}], rem[{}]".format(num_bytes, associativity,
    #        self.bitwidth_cacheline//8, self.bitwidth_tag, self.bitwidth_index,
    #        self.bitwidth_tag_remainder) )

    #--------------------------------------------------------------------
    # Make Bits object
    #--------------------------------------------------------------------

    self.BitsLen           = mk_bits( self.bitwidth_len )           # Number of bytes  being accessed
    self.BitsOpaque        = mk_bits( self.bitwidth_opaque )        # opaque
    self.BitsType          = mk_bits( 4 )                           # access type
    self.BitsAddr          = mk_bits( self.bitwidth_addr )          # address
    self.BitsData          = mk_bits( self.bitwidth_data )          # data
    self.BitsCacheline     = mk_bits( self.bitwidth_cacheline )     # cacheline
    self.BitsIdx           = mk_bits( self.bitwidth_index )         # index
    self.BitsTag           = mk_bits( self.bitwidth_tag )           # tag
    self.BitsOffset        = mk_bits( self.bitwidth_offset )        # offset
    self.BitsTagArray      = mk_bits( self.bitwidth_tag_array )     # Tag array write byte enable
    self.BitsTagArrayTmp   = mk_bits( self.bitwidth_tag_remainder ) # number of bits free in tag array
    self.BitsTagWben       = mk_bits( self.bitwidth_tag_wben )      # Tag array write bit enable
    self.BitsDataWben      = mk_bits( self.bitwidth_data_wben )     # Data array write bit enable
    self.BitsRdDataMuxSel  = mk_bits( self.bitwidth_rd_data_mux_sel ) 
#    self.BitsRdWordMuxSel  = mk_bits( self.bitwidth_rd_word_mux_sel ) 
    self.BitsRd2ByteMuxSel = mk_bits( self.bitwidth_rd_2byte_mux_sel )
    self.BitsRdByteMuxSel  = mk_bits( self.bitwidth_rd_byte_mux_sel )
    self.BitsAssoc         = mk_bits( self.associativity )
    self.BitsAssoclog2     = mk_bits( self.bitwidth_clog_asso )
    self.BitsClogNlines    = mk_bits( clog2(self.total_num_cachelines) )
    self.BitsNlinesPerWay  = mk_bits( self.nblocks_per_way )
    self.BitsMemLen        = mk_bits( self.bitwidth_mem_len )

    # Cifer Bits objects
    self.BitsVal           = mk_bits( self.bitwidth_val )
    self.BitsDirty         = mk_bits( self.bitwidth_dirty )

    #--------------------------------------------------------------------
    # Specialize structs
    #--------------------------------------------------------------------

    self.StructAddr      = mk_addr_struct( self )

    #--------------------------------------------------------------------
    # Msgs for Dpath
    #--------------------------------------------------------------------
    # sram is "full" if each bit is used for either tag, valid, or dirty
    self.full_sram = False if (self.bitwidth_tag_array - self.bitwidth_tag - self.bitwidth_dirty - self.bitwidth_val) > 0 else True
    self.StructStatus = mk_dpath_status_struct( self )

    # Structs used within dpath module
    self.PipelineMsg    = mk_pipeline_msg( self )
    self.MSHRMsg        = mk_MSHR_msg( self )
    self.StructTagArray = mk_tag_array_struct( self )
    self.StructHit      = mk_hit_stall_struct( self )

    #--------------------------------------------------------------------
    # Msgs for Ctrl
    #--------------------------------------------------------------------

    self.StructCtrl = mk_ctrl_signals_struct( self )

    # Structs local to the ctrl
    self.CtrlMsg = mk_ctrl_pipeline_struct()
    self.BitsCtrlStates = mk_bits(clog2(6))

    #--------------------------------------------------------------------
    # Default Values
    #--------------------------------------------------------------------
    # TEMP NAMES: Will come up with something
    self.wdmx0 = self.BitsRdDataMuxSel(0)
    self.btmx0 = self.BitsRdByteMuxSel(0)
    self.bbmx0 = self.BitsRd2ByteMuxSel(0)
    self.acmx0 = Bits2(0) # access select 0
    self.wben0 = self.BitsDataWben(0)
    self.wbenf = self.BitsDataWben(-1)
    self.tg_wbenf = self.BitsTagWben(-1)

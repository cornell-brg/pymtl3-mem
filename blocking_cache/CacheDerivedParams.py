"""
=========================================================================
CacheDerivedParams.py
=========================================================================
Generates constants and bitstructs from cache parameters

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   10 February 2020
"""

from pymtl3 import *
from mem_pclib.ifcs.cacheStructs   import *

class CacheDerivedParams:

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
    self.bitwidth_data             = CacheReqType.get_field_type("addr").nbits
    # Convert to total number of bits and then divide 
    self.total_num_cachelines      = self.num_bytes * 8 // self.bitwidth_cacheline      
    self.nblocks_per_way           = self.total_num_cachelines // self.associativity # cachelines per way
    self.bitwidth_index            = clog2( self.nblocks_per_way )                   # index width
    self.bitwidth_offset           = clog2( self.bitwidth_cacheline // 8 )           # offset bitwidth
    self.bitwidth_tag              = self.bitwidth_addr - self.bitwidth_offset - self.bitwidth_index # tag bitwidth
    # 1 bit for dirty and val. Rest for tag. Need to make sure multiple of 8.
    self.bitwidth_tag_array        = int( self.bitwidth_tag + 1 + 1 + 7 ) // 8 * 8
    self.bitwidth_tag_wben         = int( self.bitwidth_tag_array + 7 ) // 8         # Tag array write byte bitwidth
    self.bitwidth_data_wben        = int( self.bitwidth_cacheline + 7 ) // 8         # Data array write byte bitwidth
    self.bitwidth_rd_wd_mux_sel    = clog2( self.bitwidth_cacheline // self.bitwidth_data + 1 ) # Read word mux bitwidth
    self.bitwidth_rd_byte_mux_sel  = clog2( self.bitwidth_data // 8 )                # Read byte mux sel bitwidth
    self.bitwidth_rd_2byte_mux_sel = clog2( self.bitwidth_data // 16 )               # Read half word mux sel bitwidth
    self.bitwidth_len              = clog2( self.bitwidth_data // 8 )
    if self.associativity == 1:
      self.bitwidth_clog_asso      = 1
    else:
      self.bitwidth_clog_asso      = clog2( self.associativity )

    print("size[{}], asso[{}], clw[{}], tag[{}], idx[{}]".format(num_bytes, associativity,
    self.bitwidth_cacheline//8, self.bitwidth_tag, self.bitwidth_index))

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
    self.BitsTagArrayTmp   = mk_bits( self.bitwidth_tag_array - self.bitwidth_tag - 2 )
    self.BitsTagwben       = mk_bits( self.bitwidth_tag_wben )      # Tag array write byte enable
    self.BitsDataWben      = mk_bits( self.bitwidth_data_wben )     # Data array write byte enable
    self.BitsRdWordMuxSel  = mk_bits( self.bitwidth_rd_wd_mux_sel ) # Read data mux M2
    self.BitsRd2ByteMuxSel = mk_bits( self.bitwidth_rd_2byte_mux_sel )
    self.BitsRdByteMuxSel  = mk_bits( self.bitwidth_rd_byte_mux_sel )
    self.BitsAssoc         = mk_bits( self.associativity )
    self.BitsAssoclog2     = mk_bits( self.bitwidth_clog_asso )
    self.BitsClogNlines    = mk_bits(clog2(self.total_num_cachelines))

    #--------------------------------------------------------------------
    # Specialize structs
    #--------------------------------------------------------------------

    self.StructAddr      = mk_addr_struct( self )

    #--------------------------------------------------------------------
    # Msgs for Dpath
    #--------------------------------------------------------------------

    self.full_sram = False if self.bitwidth_tag_array - self.bitwidth_tag \
      - 2 > 0 else True
    self.StructStatus = mk_dpath_status_struct( self )

    # Structs used within dpath module
    self.PipelineMsg    = mk_pipeline_msg( self )
    self.MSHRMsg        = mk_MSHR_msg( self )
    self.StructTagArray = mk_tag_array_struct( self )

    #--------------------------------------------------------------------
    # Msgs for Ctrl
    #--------------------------------------------------------------------

    self.StructCtrl = mk_ctrl_signals_struct( self )

    # Structs local to the ctrl
    self.CtrlMsg = mk_ctrl_pipeline_struct()

    #--------------------------------------------------------------------
    # Default Values
    #--------------------------------------------------------------------
    # TEMP NAMES: Will come up with something
    self.wdmx0 = self.BitsRdWordMuxSel(0)
    self.btmx0 = self.BitsRdByteMuxSel(0)
    self.bbmx0 = self.BitsRd2ByteMuxSel(0)
    self.acmx0 = Bits2(0) # access select 0
    self.wben0 = self.BitsDataWben(0)
    self.wbenf = self.BitsDataWben(-1)
    self.tg_wbenf = self.BitsTagwben(-1)

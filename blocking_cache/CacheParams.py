'''
CacheParams

Author: Eric Tang (et396), Xiaoyu Yan (xy97) 
Date:   10 February 2020
'''

from pymtl3 import *
from mem_pclib.ifcs.dpathStructs   import *
from mem_pclib.ifcs.ctrlStructs    import *
from mem_pclib.ifcs.cacheStructs   import *

class CacheParams:

  def __init__(self,    
    num_bytes     = 4096, # cache size in bytes
    CacheMsg      = "",   # Cache req/resp msg type
    MemMsg        = "",   # Memory req/resp msg type
    associativity = 1     # Associativity
  ):

    self.num_bytes     = num_bytes
    self.CacheMsg      = CacheMsg
    self.MemMsg        = MemMsg
    self.associativity = associativity

    #--------------------------------------------------------------------------
    # Bitwidths
    #--------------------------------------------------------------------------

    self.bitwidth_cacheline        = MemMsg.bitwidth_data
    self.bitwidth_addr             = MemMsg.bitwidth_addr
    self.bitwidth_opaque           = MemMsg.bitwidth_opaque
    self.bitwidth_data             = CacheMsg.bitwidth_data
    self.total_num_cachelines      = self.num_bytes // self.bitwidth_cacheline             # number of cachelines
    self.nblocks_per_way           = self.total_num_cachelines // self.associativity       # cachelines per way
    self.bitwidth_index            = clog2( self.nblocks_per_way )                         # index width
    self.bitwidth_offset           = clog2( self.bitwidth_cacheline // 8 )                 # offset bitwidth
    self.bitwidth_tag              = self.bitwidth_addr - self.bitwidth_offset - self.bitwidth_index # tag bitwidth
    self.bitwidth_tag_array        = int( self.bitwidth_tag + 1 + 1 + 7 ) // 8 * 8 
    self.bitwidth_tag_wben         = int( self.bitwidth_tag_array + 7 ) // 8               # Tag array write byte bitwidth
    self.bitwidth_data_wben        = int( self.bitwidth_cacheline + 7 ) // 8               # Data array write byte bitwidth 
    self.bitwidth_rd_wd_mux_sel    = clog2( self.bitwidth_cacheline // self.bitwidth_data + 1 ) # Read word mux bitwidth
    self.bitwidth_rd_byte_mux_sel  = clog2( self.bitwidth_data // 8 )                      # Read byte mux sel bitwidth
    self.bitwidth_rd_2byte_mux_sel = clog2( self.bitwidth_data // 16 )                     # Read half word mux sel bitwidth
    self.bitwidth_len              = clog2( self.bitwidth_data // 8 )
    if self.associativity == 1:
      self.bitwidth_clog_asso      = 1
    else:
      self.bitwidth_clog_asso      = clog2( self.associativity ) 
   
    #--------------------------------------------------------------------
    # Make Bits object
    #--------------------------------------------------------------------

    self.BitsLen           = mk_bits(self.bitwidth_len)       # Number of bytes  being accessed
    self.BitsOpaque        = mk_bits(self.bitwidth_opaque)    # opaque
    self.BitsType          = mk_bits(4)                       # access type
    self.BitsAddr          = mk_bits(self.bitwidth_addr)           # address 
    self.BitsData          = mk_bits(self.bitwidth_data)           # data 
    self.BitsCacheline     = mk_bits(self.bitwidth_cacheline)      # cacheline 
    self.BitsIdx           = mk_bits(self.bitwidth_index)          # index 
    self.BitsTag           = mk_bits(self.bitwidth_tag)            # tag 
    self.BitsOffset        = mk_bits(self.bitwidth_offset)         # offset 
    self.BitsTagArray      = mk_bits(self.bitwidth_tag_array)      # Tag array write byte enable
    self.BitsTagwben       = mk_bits(self.bitwidth_tag_wben)       # Tag array write byte enable
    self.BitsDataWben      = mk_bits(self.bitwidth_data_wben)      # Data array write byte enable
    self.BitsRdWordMuxSel  = mk_bits(self.bitwidth_rd_wd_mux_sel)  # Read data mux M2 
    self.BitsRdByteMuxSel  = mk_bits(self.bitwidth_rd_byte_mux_sel)
    self.BitsRd2ByteMuxSel = mk_bits(self.bitwidth_rd_2byte_mux_sel)
    self.BitsAssoc         = mk_bits(self.associativity)
    self.BitsAssoclog2     = mk_bits(self.bitwidth_clog_asso)

    #--------------------------------------------------------------------
    # Msgs for Dpath
    #--------------------------------------------------------------------
    
    self.DpathSignalsOut = mk_dpath_signals_out_struct(self)

    # structs local to the dpath
    
    self.PipelineMsg = mk_pipeline_msg(self.bitwidth_addr, \
      self.bitwidth_cacheline, self.bitwidth_opaque, 4, self.bitwidth_len)
    self.MSHRMsg     = mk_MSHR_msg(self.bitwidth_addr, \
      self.bitwidth_data, self.bitwidth_opaque, 4, self.bitwidth_len, \
        self.bitwidth_clog_asso)
    self.MuxM0Msg    = mk_M0_mux_msg(self)

    #--------------------------------------------------------------------
    # Msgs for Ctrl
    #--------------------------------------------------------------------
    
    self.CtrlSignalsOut = mk_ctrl_signals_out_struct(self)

    # structs local to the ctrl
    
    self.CtrlMsg = mk_ctrl_pipeline_struct()
    
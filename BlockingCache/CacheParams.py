'''
CacheParams

Author: Eric Tang (et396), Xiaoyu Yan (xy97) 
Date:   10 February 2020
'''

from pymtl3 import *

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
	  self.total_num_cachelines      = num_bytes // bitwidth_cacheline                  # number of cachelines
	  self.nblocks_per_way           = total_num_cachelines // associativity            # cachelines per way
	  self.bitwidth_index            = clog2( nblocks_per_way )                         # index width
	  self.bitwidth_offset           = clog2( bitwidth_cacheline // 8 )                 # offset bitwidth
	  self.bitwidth_tag              = bitwidth_addr - bitwidth_offset - bitwidth_index # tag bitwidth
	  self.bitwidth_tag_array        = int( bitwidth_tag + 1 + 1 + 7 ) // 8 * 8 
	  self.bitwidth_tag_wben         = int( bitwidth_tag_array + 7 ) // 8               # Tag array write byte bitwidth
	  self.bitwidth_data_wben        = int( bitwidth_cacheline + 7 ) // 8               # Data array write byte bitwidth 
	  self.bitwidth_rd_wd_mux_sel    = clog2( bitwidth_cacheline // bitwidth_data + 1 ) # Read word mux bitwidth
	  self.bitwidth_rd_byte_mux_sel  = clog2( bitwidth_data // 8 )                      # Read byte mux sel bitwidth
	  self.bitwidth_rd_2byte_mux_sel = clog2( bitwidth_data // 16 )                     # Read half word mux sel bitwidth
	
	  #--------------------------------------------------------------------------
	  # Make Bits object
	  #--------------------------------------------------------------------------
	
	  self.BitsLen           = mk_bits(clog2(bitwidth_data//8)) # Number of bytes  being accessed
	  self.BitsOpaque        = mk_bits(bitwidth_opaque)         # opaque
	  self.BitsType          = mk_bits(4)                       # access type
	  self.BitsAddr          = mk_bits(bitwidth_addr)           # address 
	  self.BitsData          = mk_bits(bitwidth_data)           # data 
	  self.BitsCacheline     = mk_bits(bitwidth_cacheline)      # cacheline 
	  self.BitsIdx           = mk_bits(bitwidth_index)          # index 
	  self.BitsTag           = mk_bits(bitwidth_tag)            # tag 
	  self.BitsOffset        = mk_bits(bitwidth_offset)         # offset 
	  self.BitsTagArray      = mk_bits(bitwidth_tag_array)      # Tag array write byte enable
	  self.BitsTagwben       = mk_bits(bitwidth_tag_wben)       # Tag array write byte enable
	  self.BitsDataWben      = mk_bits(bitwidth_data_wben)      # Data array write byte enable
	  self.BitsRdWordMuxSel  = mk_bits(bitwidth_rd_wd_mux_sel)  # Read data mux M2 
	  self.BitsRdByteMuxSel  = mk_bits(bitwidth_rd_byte_mux_sel)
	  self.BitsRd2ByteMuxSel = mk_bits(bitwidth_rd_2byte_mux_sel)
	  self.BitsAssoc         = mk_bits(associativity)
	  if associativity == 1:
	    self.BitsAssoclog2 = Bits1
	  else:
	    self.BitsAssoclog2  = mk_bits(clog2(associativity))
	

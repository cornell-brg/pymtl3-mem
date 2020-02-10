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

	  #--------------------------------------------------------------------------
	  # Bitwidths
	  #--------------------------------------------------------------------------
	
	  bitwidth_cacheline        = MemMsg.bitwidth_data
	  bitwidth_addr             = MemMsg.bitwidth_addr
	  bitwidth_opaque           = MemMsg.bitwidth_opaque
	  bitwidth_data             = CacheMsg.bitwidth_data
	  total_num_cachelines      = num_bytes // bitwidth_cacheline                  # number of cachelines
	  nblocks_per_way           = total_num_cachelines // associativity            # cachelines per way
	  bitwidth_index            = clog2( nblocks_per_way )                         # index width
	  bitwidth_offset           = clog2( bitwidth_cacheline // 8 )                 # offset bitwidth
	  bitwidth_tag              = bitwidth_addr - bitwidth_offset - bitwidth_index # tag bitwidth
	  bitwidth_tag_array        = int( bitwidth_tag + 1 + 1 + 7 ) // 8 * 8 
	  bitwidth_tag_wben         = int( bitwidth_tag_array + 7 ) // 8               # Tag array write byte bitwidth
	  bitwidth_data_wben        = int( bitwidth_cacheline + 7 ) // 8               # Data array write byte bitwidth 
	  bitwidth_rd_wd_mux_sel    = clog2( bitwidth_cacheline // bitwidth_data + 1 ) # Read word mux bitwidth
	  bitwidth_rd_byte_mux_sel  = clog2( bitwidth_data // 8 )                      # Read byte mux sel bitwidth
	  bitwidth_rd_2byte_mux_sel = clog2( bitwidth_data // 16 )                     # Read half word mux sel bitwidth
	
	  #--------------------------------------------------------------------------
	  # Make Bits object
	  #--------------------------------------------------------------------------
	
	  BitsLen           = mk_bits(clog2(bitwidth_data//8)) # Number of bytes  being accessed
	  BitsOpaque        = mk_bits(bitwidth_opaque)         # opaque
	  BitsType          = mk_bits(4)                       # access type
	  BitsAddr          = mk_bits(bitwidth_addr)           # address 
	  BitsData          = mk_bits(bitwidth_data)           # data 
	  BitsCacheline     = mk_bits(bitwidth_cacheline)      # cacheline 
	  BitsIdx           = mk_bits(bitwidth_index)          # index 
	  BitsTag           = mk_bits(bitwidth_tag)            # tag 
	  BitsOffset        = mk_bits(bitwidth_offset)         # offset 
	  BitsTagArray      = mk_bits(bitwidth_tag_array)      # Tag array write byte enable
	  BitsTagwben       = mk_bits(bitwidth_tag_wben)       # Tag array write byte enable
	  BitsDataWben      = mk_bits(bitwidth_data_wben)      # Data array write byte enable
	  BitsRdWordMuxSel  = mk_bits(bitwidth_rd_wd_mux_sel)  # Read data mux M2 
	  BitsRdByteMuxSel  = mk_bits(bitwidth_rd_byte_mux_sel)
	  BitsRd2ByteMuxSel = mk_bits(bitwidth_rd_2byte_mux_sel)
	  BitsAssoc         = mk_bits(associativity)
	  if associativity == 1:
	    BitsAssoclog2 = Bits1
	  else:
	    BitsAssoclog2  = mk_bits(clog2(associativity))
	
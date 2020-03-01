"""
#=========================================================================
# addrDecoder.py
#=========================================================================

Decodes address to its various parts and put it into a bitstruct
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 12 February 2020
"""

from pymtl3 import *

class AddrDecoder (Component):

  def construct( s, p ):

    s.addr_in   = InPort(p.BitsAddr)
    s.out       = OutPort(p.StructAddr)
    
    offset_end = p.bitwidth_offset
    index_end  = p.bitwidth_index + p.bitwidth_offset
    tag_end    = p.bitwidth_addr
    s.out.offset //= s.addr_in[ 0          : offset_end ]
    s.out.index  //= s.addr_in[ offset_end : index_end ]
    s.out.tag    //= s.addr_in[ index_end  : tag_end   ]

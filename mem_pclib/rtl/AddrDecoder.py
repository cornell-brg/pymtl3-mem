"""
#=========================================================================
# addrDecoder.py
#=========================================================================

Decodes address to its various parts
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 12 February 2020
"""

from pymtl3 import *

class AddrDecoder (Component):

  def construct( s, param ):

    s.addr_in   = InPort(param.BitsAddr)
    s.tag_out   = OutPort(param.BitsTag)
    s.index_out = OutPort(param.BitsIdx)
    s.offset_out= OutPort(param.BitsOffset)

    offset_end = param.bitwidth_offset
    index_end  = param.bitwidth_index + param.bitwidth_offset
    tag_end    = param.bitwidth_addr
    s.offset_out //= s.addr_in[ 0          : offset_end ]
    s.index_out  //= s.addr_in[ offset_end : index_end ]
    s.tag_out    //= s.addr_in[ index_end  : tag_end   ]
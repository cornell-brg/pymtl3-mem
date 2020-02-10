"""
#=========================================================================
# ReqRespMsgTypes.py
#=========================================================================
Unified req, Resp msg classes

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : November 4, 2019
"""

from pymtl3.stdlib.ifcs.MemMsg import mk_mem_msg

#-------------------------------------------------------------------------
# ReqRespMsgTypes
#-------------------------------------------------------------------------

class ReqRespMsgTypes():
  def __init__(s, opq, addr, data):
    s.Req, s.Resp     = mk_mem_msg(opq, addr, data)
    s.bitwidth_opaque = opq
    s.bitwidth_addr   = addr
    s.bitwidth_data   = data


"""
#=========================================================================
# ReqRespMsgTypes.py
#=========================================================================
Unified req, Resp msg classes

Author : Xiaoyu Yan, Eric Tang
Date   : 11/04/19
"""

from pymtl3.stdlib.ifcs.MemMsg import mk_mem_msg

#-------------------------------------------------------------------------
# ReqRespMsgTypes
#-------------------------------------------------------------------------

class ReqRespMsgTypes():
  def __init__(s, opq, addr, data):
    s.Req, s.Resp = mk_mem_msg(opq, addr, data)
    s.obw = opq
    s.abw = addr
    s.dbw = data


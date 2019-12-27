"""
#=========================================================================
# ReplacementPolicy.py
#=========================================================================
Implement replacement depending on which replacement policies chosen

Author : Xiaoyu Yan, Eric Tang
Date   : 12/23/19
"""

from pymtl3                         import *
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvIfcRTL
from pymtl3.stdlib.ifcs.MemMsg      import MemMsgType, mk_mem_msg
from pymtl3.stdlib.rtl.registers import RegEnRst, RegRst

class ReplacementPolicy (Component):
  def construct(s,
                BitsAssoc     = "inv",
                BitsAssoclog2 = "inv",
                associativity = 1,
                policy        = 0, # what policy to use? LRU for now
  ):
    s.repreq_en = InPort(Bits1)
    s.repreq_rdy = OutPort(Bits1)
    s.repreq_hit_ptr = InPort(BitsAssoclog2)
    s.repreq_is_hit  = InPort(Bits1)
    s.repreq_ptr     = InPort(BitsAssoclog2)
    s.represp_ptr   = OutPort(BitsAssoclog2)

    s.repreq_rdy //= b1(1)

    # hits and misses
    # print(associativity, policy)
    if associativity == 2:
      if policy == 0: # LRU - flip bit when hit or miss
        @s.update
        def logic():
          if s.reset:
            s.represp_ptr = BitsAssoclog2(0)
          else:
            s.represp_ptr = s.repreq_ptr
            if s.repreq_en:
              if not s.repreq_is_hit:
                s.represp_ptr = ~s.repreq_ptr
              elif s.repreq_is_hit:
                s.represp_ptr = ~s.repreq_hit_ptr
    else:
      # dmapped
      s.represp_ptr //= b1(0)

  def line_trace( s ):
    msg = ""
    # msg += f" hit-in:{s.repreq_hit_ptr}"
    return msg
          
    



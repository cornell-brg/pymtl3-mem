"""
#=========================================================================
# ReplacementPolicy.py
#=========================================================================
Implement replacement depending on which replacement policies chosen

Author : Xiaoyu Yan, Eric Tang
Date   : 11/18/19
"""

from pymtl3                         import *
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvIfcRT

class ReplacementPolicy (Component):
  def construct(s,
                BitsAssoc     = "inv",
                BitsAssoclog2 = "inv",
                associativity = 1,
                policy        = 0,
  ):
    s.replacereq = RecvIfcRTL(BitsAssoc)
    s.replace_ptr = OutPort(BitsAssoclog2)

    s.replacereq.rdy //= b1(1)

    @s.update
    def logic():
      if s.replacereq.en:
        if associativity == 2:
          hitmask = s.replacereq.msg
          if hitmask[0] and not hitmask[1]:
            s.replace_ptr = BitsAssoclog2(1)
          elif hitmask[1] and not hitmask[0]:
            s.replace_ptr = BitsAssoclog2(0)
          else:
            s.replace_ptr = not s.replace_ptr



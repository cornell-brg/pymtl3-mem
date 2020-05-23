"""
#=========================================================================
# ReplacementPolicy.py
#=========================================================================
Implement replacement depending on which replacement policies chosen

Author : Xiaoyu Yan, Eric Tang
Date   : 12/23/19
"""

from pymtl3                  import *
from pymtl3.stdlib.basic_rtl import RegEnRst, RegRst

class ReplacementPolicy (Component):
  """
  Given an input of histories for past accesses (LRU bits),
  output the way number that should have its cache line
  replaced.

  Latency sensitive - do not expect to be problems?
  Base two associativity only
  """
  def construct(s,
                BitsAssoc     = "inv",
                BitsAssoclog2 = "inv",
                associativity = 1,
                policy        = 0, # what policy to use? LRU for now
  ):
    # policy 0 = LRU policy
    # More area efficient policies include FIFO
    s.repreq_en      = InPort()
    s.repreq_rdy     = OutPort()
    s.repreq_hit_ptr = InPort(BitsAssoclog2)
    s.repreq_is_hit  = InPort()
    s.repreq_ptr     = InPort(BitsAssoclog2)
    s.represp_ptr    = OutPort(BitsAssoclog2)

    s.repreq_rdy //= 1

    # hits and misses
    # print(associativity, policy)
    if associativity == 2:
      # if policy == 0: # LRU - flip bit when hit or miss
      # LRU for 2 way is extra simple since we don't need
      # to keep track
      @update
      def pointer_logic():
        s.represp_ptr @= s.repreq_ptr
        if s.repreq_en:
          if ~s.repreq_is_hit:
            s.represp_ptr @= ~s.repreq_ptr
          elif s.repreq_is_hit:
            s.represp_ptr @= ~s.repreq_hit_ptr
    else:
      # Real difficult to implement LRU here
      s.represp_ptr //= b1(0)

  def line_trace( s ):
    msg = ""
    # msg += f" hit-in:{s.repreq_hit_ptr}"
    return msg

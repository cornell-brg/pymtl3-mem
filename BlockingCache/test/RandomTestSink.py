"""
=========================================================================
RandomTestSink.py
=========================================================================
Random Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 20 November 2019
"""
from pymtl3      import *
from collections import deque
from pymtl3.stdlib.ifcs import RecvIfcRTL, RecvRTL2SendCL, enrdy_to_str


class RandomTestSink( Components ):
  def construct(s, type, delay):
    s.DUT_recv = RecvIfcRTL( Type )
    s.REF_recv = RecvIfcRTL( Type )

    s.REF_resp = deque([])
    s.DUT_resp = deque([])

    s.DUT_recv.rdy //= b1(1)
    s.REF_recv.rdy //= b1(1)
    if s.DUT_recv.en:
      s.DUT_resp.appendleft(s.DUT_recv.msg)
    if s.REF_recv.en:
      s.REF_recv.appendleft(s.REF_recv.msg)

    

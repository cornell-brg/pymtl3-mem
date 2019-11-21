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


class RandomTestSink( Component ):
  def construct(s, Type, delay, msg_length):
    s.DUT_recv = RecvIfcRTL( Type )
    s.REF_recv = RecvIfcRTL( Type )
    s.DUT_len = s.REF_len = 0
    s.REF_resp = deque([])
    s.DUT_resp = deque([])

    s.DUT_recv.rdy //= b1(1)
    s.REF_recv.rdy //= b1(1)
    @s.update
    def update_logic():
      if s.DUT_recv.en:
        s.DUT_resp.appendleft(s.DUT_recv.msg)
        s.DUT_len = s.DUT_len + 1
      if s.REF_recv.en:
        s.REF_resp.appendleft(s.REF_recv.msg)
        s.REF_len = s.REF_len + 1
      if s.DUT_len > 0 and s.REF_len > 0:
        dut_resp = s.DUT_resp.pop()
        ref_resp = s.REF_resp.pop()
        # print ("{}?={}".format(dut_resp,ref_resp))
        # assert  dut_resp==ref_resp, \
        # "{}!={}".format(dut_resp,ref_resp)
      
      
      
  def done(s):
    return s.DUT_len == 2 and s.REF_len == 2

  def line_trace(s):
    msg = "[{}]{}<->[{}]{}  dut[{}]  |  ref[{}]".format(\
      s.DUT_recv.en, s.DUT_recv.msg,s.REF_recv.en,\
        s.REF_recv.msg,s.DUT_resp,s.REF_resp
        ) 
    # if s.DUT_len > 1 and s.REF_len > 1:
    #   msg = "{}<->{}".format(s.DUT_resp,s.REF_resp)
    # else:
    #   msg = ""
    # print("dut[{}]|ref[{}]".format(s.DUT_resp,s.REF_resp))
        
    return msg
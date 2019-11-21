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

from pymtl3.stdlib.rtl.registers    import RegRst

class RandomTestSink( Component ):
  def construct(s, Type, delay, msg_length):
    s.REF_resp = [Wire(Type) for _ in range(msg_length+1)]
    s.DUT_resp = [Wire(Type) for _ in range(msg_length+1)]
    s.DUT_recv = RecvIfcRTL( Type )
    s.REF_recv = RecvIfcRTL( Type )
    s.dut_r = Wire(Type)
    s.ref_r = Wire(Type)
    s.DUT_recv.rdy //= b1(1)
    s.REF_recv.rdy //= b1(1)
    s.msg_length = msg_length

    queue = deque([])

    BitsLen = mk_bits(clog2(msg_length+1))
    s.DUT_len_out = Wire(BitsLen)
    # s.DUT_len_in_ = Wire(BitsLen)
    # s.DUT_len_reg = RegRst(BitsLen)(
    #   out = s.DUT_len_out,
    #   in_ = s.DUT_len_in_ 
    # )
    s.REF_len_out = Wire(BitsLen)
    # s.REF_len_in_ = Wire(BitsLen)
    # s.REF_len_reg = RegRst(BitsLen)(
    #   out = s.REF_len_out,
    #   in_ = s.REF_len_in_
    # )
    # s.DUT_top_out = Wire(BitsLen)
    # s.DUT_top_in_ = Wire(BitsLen)
    # s.DUT_top_reg = RegRst(BitsLen)(
    #   out = s.DUT_top_out,
    #   in_ = s.DUT_top_in_ 
    # )
    # s.REF_top_out = Wire(BitsLen)
    # s.REF_top_in_ = Wire(BitsLen)
    # s.REF_top_reg = RegRst(BitsLen)(
    #   out = s.REF_top_out,
    #   in_ = s.REF_top_in_
    # )

    @s.update
    def comb_logic():
      if s.DUT_recv.en:
        # s.DUT_resp[s.DUT_len_out] = s.DUT_recv.msg
        s.DUT_resp[s.DUT_len_out] = s.DUT_recv.msg

      if s.REF_recv.en:
        # s.REF_resp[s.REF_len_out] = s.REF_recv.msg
        s.REF_resp[s.REF_len_out] = s.REF_recv.msg
    @s.update_ff
    def comb_logic2():
      if s.DUT_recv.en:
        
        # s.DUT_len_out <<= s.DUT_len_out + BitsLen(1)
        s.DUT_len_out <<= s.DUT_len_out + BitsLen(1)

      if s.REF_recv.en:
        s.REF_len_out <<= s.REF_len_out + BitsLen(1)
      

    # s.add_constraints(
    #   U( comb_logic2 ) < U( comb_logic ),
    # )
      # if s.DUT_len_out > 0 and s.REF_len_out > 0:
      #   s.dut_r = DUT_resp.pop()
      #   s.ref_r = REF_resp.pop()
      #   assert s.DUT_resp[s.DUT_top_out]==s.REF_resp[s.REF_top_out], \
      # "{}!={}".format(s.DUT_resp[s.DUT_top_out],s.REF_resp[s.REF_top_out])
        # s.DUT_top_in_ = s.DUT_top_out + BitsLen(1)
        # s.REF_top_in_ = s.REF_top_out + BitsLen(1)

  def done(s):
    return s.DUT_len_out == s.msg_length and s.REF_len_out == s.msg_length

  def line_trace(s):
    msg = "[{}]{}<->[{}]{}  DUT_LEN:{}|REF_LEN:{} D[{},{}] R[{},{}]".format(\
      s.DUT_recv.en, s.DUT_recv.msg,s.REF_recv.en,\
        s.REF_recv.msg, s.DUT_len_out, s.REF_len_out, s.DUT_resp[0],s.DUT_resp[1],\
          s.REF_resp[0],s.REF_resp[1]
        ) 
    # msg = "[{}]{}<->[{}]{}  DUT|{}|{} REF|{}|{} | DUT:{} REF:{}".format(\
    #   s.DUT_recv.en, s.DUT_recv.msg,s.REF_recv.en,\
    #     s.REF_recv.msg, s.DUT_len_out, s.DUT_top_out, s.REF_len_out,\
    #       s.REF_top_out,s.DUT_resp[s.DUT_top_out],\
    #         s.REF_resp[s.REF_top_out]
    #     ) 
    # msg = ""
    return msg
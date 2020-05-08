"""
=========================================================================
HypothesisTest.py
=========================================================================
Hypothesis test with cache
Now with Latencies!!

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 25 December 2019  Merry Christmas!! UWU
"""

import hypothesis
from hypothesis          import strategies as st
from pymtl3              import *
from mem_ifcs.MemMsg     import MemMsgType, mk_mem_msg
from constants.constants import *
from test.sim_utils      import rand_mem
from ..BlockingCacheFL   import ModelCache

@st.composite
def gen_reqs( draw, addr_min, addr_max, clw, dbw ):
  type_ranges = draw( st.integers( 0, 2 ) )
  if type_ranges == 0:
    type_ = draw( st.sampled_from([
      MemMsgType.READ,
      MemMsgType.WRITE,
      MemMsgType.AMO_ADD,
      MemMsgType.AMO_AND,
      MemMsgType.AMO_OR,
      MemMsgType.AMO_SWAP,
      MemMsgType.AMO_MIN,
      MemMsgType.AMO_MINU,
      MemMsgType.AMO_MAX,
      MemMsgType.AMO_MAXU,
      MemMsgType.AMO_XOR,
    ]), label='type')
  elif type_ranges == 1:
    type_ = draw( st.sampled_from([
      MemMsgType.READ,
      MemMsgType.WRITE,
      MemMsgType.INV,
      MemMsgType.FLUSH,
    ]), label="type" )
  else:
    type_ = draw( st.sampled_from([
      MemMsgType.READ,
      MemMsgType.WRITE,
      MemMsgType.AMO_ADD,
      MemMsgType.AMO_AND,
      MemMsgType.AMO_OR,
      MemMsgType.AMO_SWAP,
      MemMsgType.AMO_MIN,
      MemMsgType.AMO_MINU,
      MemMsgType.AMO_MAX,
      MemMsgType.AMO_MAXU,
      MemMsgType.AMO_XOR,
      MemMsgType.INV,
      MemMsgType.FLUSH,
    ]), label="type" )
  if type_ == MemMsgType.INV or type_ == MemMsgType.FLUSH:
    addr = Bits32(0)
    len_ = 0
    data = 0
  else:
    data = draw( st.integers(0, 0xffffffff), label="data" )
    addr = Bits32(draw( st.integers(addr_min, addr_max), label="addr" ))
    if type_ >= MemMsgType.AMO_ADD and type_ <= MemMsgType.AMO_XOR:
      addr = addr & Bits32(0xfffffffc)
      if dbw == 32:
        len_ = 0
      else:
        len_ = 4
    else:
      max_len_order = clog2(dbw//8)
      if type_ == MemMsgType.WRITE:
        max_len_order = 2
      len_order = draw( st.integers(0, max_len_order), label="len" )
      len_ = 2**len_order
      if len_ == 2:
        addr = addr & Bits32(0xfffffffe)
      elif len_ == 4:
        addr = addr & Bits32(0xfffffffc)
      elif len_ == 8:
        addr = addr & Bits32(0xfffffff8)
      elif len_ == 16:
        addr = addr & Bits32(0xfffffff0)
      elif len_ == 32:
        addr = addr & Bits32(0xffffffe0)
      # len_ = int(BitsLen(len_))
    bitwidth_len = clog2(dbw >> 3)   
    len_ = Bits(bitwidth_len, len_, trunc_int=True) 
  return (addr, type_, data, len_)

class HypothesisTests:
  def hypothesis_test_harness( s, associativity, clw, dbw, num_blocks, req, stall_prob,
                               latency, src_delay, sink_delay, min_trans, cmdline_opts, 
                               max_cycles, dump_vtb, line_trace ):
    cacheSize = (clw * associativity * num_blocks) // 8
    addr_min = 0
    addr_max = int( cacheSize // 4 * 2 * associativity )
    mem = rand_mem(addr_min, addr_max)
    CacheReqType, CacheRespType = mk_mem_msg(8, 32, dbw, has_wr_mask=False)
    MemReqType, MemRespType = mk_mem_msg(8, 32, clw)
    # FL Model to generate expected transactions
    model = ModelCache( cacheSize, associativity, 0, CacheReqType, CacheRespType,
                        MemReqType, MemRespType, mem )
    # Grab list of generated transactions
    reqs_lst = req.draw(
      st.lists( gen_reqs( addr_min, addr_max, clw, dbw ), min_size=min_trans, max_size=200 ),
      label= "requests"
    )
    for i in range(len(reqs_lst)):
      addr, type_, data, len_ = reqs_lst[i]
      if type_ == MemMsgType.WRITE:
        model.write(addr, data, i, len_)
      elif type_ == MemMsgType.READ:
        model.read(addr, i, len_)
      elif type_ == MemMsgType.WRITE_INIT:
        model.init(addr, data, i, len_)
      elif type_ >= MemMsgType.AMO_ADD and type_ <= MemMsgType.AMO_XOR:
        model.amo(addr, data, i, len_, type_)
      elif type_ == MemMsgType.INV:
        model.invalidate(i)
      elif type_ == MemMsgType.FLUSH:
        model.flush(i)
      else:
        assert False, "FL model: Undefined transaction type"
    msgs = model.get_transactions() # Get FL response
    # Prepare RTL test harness
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
                associativity, cacheSize, stall_prob, latency, src_delay, sink_delay,
                cmdline_opts, max_cycles, dump_vtb, line_trace )

  @hypothesis.settings( deadline = None, max_examples = 75 )
  @hypothesis.given(
    clw_dbw      = st.sampled_from([(64,32),(64,64),(128,32),(128,64),(128,128)]),
    block_order  = st.integers( 1, 8 ),
    req          = st.data(),
    # stall_prob   = st.integers( 0 ),
    latency      = st.integers( 1, 5 ),
    src_delay    = st.integers( 0, 5 ),
    sink_delay   = st.integers( 0, 5 )
  )
  # def test_hypothesis_2way_gen( s, clw_dbw, block_order, req, stall_prob, latency, 
  #                               src_delay, sink_delay, cmdline_opts, max_cycles, 
  #                               dump_vtb, line_trace ):
  def test_hypothesis_2way_gen( s, clw_dbw, block_order, req, latency, 
                                src_delay, sink_delay, cmdline_opts, max_cycles, 
                                dump_vtb, line_trace ):
    num_blocks = 2**block_order
    clw, dbw = clw_dbw
    stall_prob = 0
    s.hypothesis_test_harness( 2, clw, dbw, num_blocks, req, stall_prob,
                               latency, src_delay, sink_delay, 1, cmdline_opts,
                               max_cycles, dump_vtb, line_trace )

  @hypothesis.settings( deadline = None, max_examples = 75 )
  @hypothesis.given(
    clw_dbw      = st.sampled_from([(64,32),(64,64),(128,32),(128,64),(128,128)]),
    block_order  = st.integers( 1, 8 ), # order of number of blocks based 2
    req          = st.data(),
    # stall_prob   = st.integers( 0 ),
    latency      = st.integers( 1, 5 ),
    src_delay    = st.integers( 0, 5 ),
    sink_delay   = st.integers( 0, 5 )
  )
  # def test_hypothesis_dmapped_gen( s, clw_dbw, block_order, req, stall_prob, latency, 
  #                                  src_delay, sink_delay, cmdline_opts, max_cycles, 
  #                                  dump_vtb, line_trace ):
  def test_hypothesis_dmapped_gen( s, clw_dbw, block_order, req, latency, 
                                   src_delay, sink_delay, cmdline_opts, max_cycles, 
                                   dump_vtb, line_trace ):
    num_blocks = 2**block_order
    clw, dbw = clw_dbw
    stall_prob = 0
    s.hypothesis_test_harness( 1, clw, dbw, num_blocks, req, stall_prob,
                               latency, src_delay, sink_delay, 1, cmdline_opts, 
                               max_cycles, dump_vtb, line_trace )

  @hypothesis.settings( deadline = None, max_examples = 30 )
  @hypothesis.given(
    req          = st.data(),
    dbw          = st.sampled_from([32,128]),
    latency      = st.integers( 1, 2 ),
    src_delay    = st.integers( 0, 2 ),
    sink_delay   = st.integers( 0, 2 )
  )
  def test_hypothesis_2way_size64_stress( s, req, dbw, latency, src_delay, sink_delay, 
                                          cmdline_opts, max_cycles, dump_vtb, line_trace ):
    s.hypothesis_test_harness( 2, 128, dbw, 2, req, 0, latency, src_delay, sink_delay,
                               30, cmdline_opts, max_cycles, dump_vtb, line_trace )

  @hypothesis.settings( deadline = None, max_examples = 30 )
  @hypothesis.given(
    req          = st.data(),
    dbw          = st.sampled_from([32,128]),
    latency      = st.integers( 1, 2 ),
    src_delay    = st.integers( 0, 2 ),
    sink_delay   = st.integers( 0, 2 )
  )
  def test_hypothesis_dmapped_size32_stress( s, req, dbw, latency, src_delay, sink_delay, 
                                          cmdline_opts, max_cycles, dump_vtb, line_trace ):
    s.hypothesis_test_harness( 1, 128, dbw, 2, req, 0, latency, src_delay, sink_delay,
                               30, cmdline_opts, max_cycles, dump_vtb, line_trace )

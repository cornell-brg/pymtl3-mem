"""
=========================================================================
 BlockingCacheFL_test.py
=========================================================================
Test for Pipelined Blocking Cache FL model

Author : Xiaoyu Yan, Eric Tang
Date   : 17 November 2019
"""
from mem_ifcs.MemMsg   import MemMsgType, mk_mem_msg
from ..BlockingCacheFL import ModelCache
from .GenericTestCases import GenericTestCases
from .AmoTests         import AmoTests
from .InvFlushTests    import InvFlushTests

class CacheFL_Tests( GenericTestCases, InvFlushTests, AmoTests ):
  def run_test( s, msgs, mem, CacheReqType, CacheRespType, MemReqType,
                MemRespType, associativity=1, cacheSize=512, stall_prob=0,
                latency=1, src_delay=0, sink_delay=0, dump_vcd=False,
                test_verilog='zeros', max_cycles=500, trace=2 ):

    cache = ModelCache( cacheSize, associativity, 0, CacheReqType, CacheRespType,
                        MemReqType, MemRespType, mem )
    src = msgs[::2]
    sink = msgs[1::2]
    for trans in src:
      if trans.type_ == MemMsgType.READ:
        cache.read(trans.addr, trans.opaque, trans.len)
      elif trans.type_ == MemMsgType.WRITE:
        cache.write(trans.addr, trans.data, trans.opaque, trans.len)
      elif trans.type_ == MemMsgType.WRITE_INIT:
        cache.init(trans.addr, trans.data, trans.opaque, trans.len)
      elif trans.type_ >= MemMsgType.AMO_ADD and trans.type_ <= MemMsgType.AMO_XOR:
        cache.amo(trans.addr, trans.data, trans.opaque, trans.len, trans.type_)
      elif trans.type_ == MemMsgType.INV:
        cache.invalidate(trans.opaque)
      elif trans.type_ == MemMsgType.FLUSH:
        cache.flush(trans.opaque)
    resps = cache.get_transactions()[1::2]
    print("")
    for i in range(len(sink)):
      print ("{:3d}: ({}) > {} ".format(i, src[i], resps[i]))
      if i < len(sink):
        assert sink[i] == resps[i], "\n  actual:{}\nexpected:{}".format(
          resps[i], sink[i]
        )

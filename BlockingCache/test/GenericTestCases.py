"""
=========================================================================
 GenericTestCases.py
=========================================================================
Cache type independent test cases for cache of any associativity

Author : Xiaoyu Yan, Eric Tang
Date   : 21 Decemeber 2019
"""

import pytest
import random
from pymtl3.stdlib.test.test_utils import mk_test_case_table
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType

from mem_pclib.ifcs.ReqRespMsgTypes import ReqRespMsgTypes
from mem_pclib.test.sim_utils import run_sim, \
translate_import, TestHarness

OBW  = 8   # Short name for opaque bitwidth
ABW  = 32  # Short name for addr bitwidth
DBW  = 32  # Short name for data bitwidth
CLW  = 128 # cacheline bitwidth
CacheMsg = ReqRespMsgTypes(OBW, ABW, DBW)
MemMsg = ReqRespMsgTypes(OBW, ABW, CLW)

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return CacheMsg.Req( type_, opaque, addr, len, data )

def resp( type_, opaque, test, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return CacheMsg.Resp( type_, opaque, test, len, data )

class CacheGeneric_Tests:

  def test_read_hit_1word(s):
    msgs = [
        #    type  opq  addr     len data                type  opq  test len data
      req( 'in', 0x0, 0x000ab000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0, 0          ),
      req( 'rd', 0x1, 0x000ab000, 0, 0          ), resp( 'rd', 0x1, 1,   0, 0xdeadbeef ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg )

  #----------------------------------------------------------------------
  # Test Case: Read Hits: path, many requests
  #----------------------------------------------------------------------
  def test_read_hit_many( s ):
    msgs = []
    for i in range(4):
      #                  type  opq  addr          len data
      msgs.append(req(  'in', i, ((0x00012000)<<2)+i*4, 0, i ))
      msgs.append(resp( 'in', i, 0,             0, 0 ))
    for i in range(4):
      msgs.append(req(  'rd', i, ((0x00012000)<<2)+i*4, 0, 0 ))
      msgs.append(resp( 'rd', i, 1,             0, i ))
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg )

  #----------------------------------------------------------------------
  # Test Case: Read Hits: random requests
  #----------------------------------------------------------------------
  def test_read_hit_random( s ):
    msgs = []
    test_amount = 4
    random.seed(1)
    addr = [random.randint(0,0x000ff) << 2 for i in range(test_amount)]
    data = [random.randint(0,0xfffff) for i in range(test_amount)]
    for i in range(test_amount):
      #                  type  opq  addr     len data
      msgs.append(req(  'in', i,   addr[i], 0,  data[i]))
      #                  type  opq  test     len data
      msgs.append(resp( 'in', i,   0,       0,  0 ))
    for i in range(test_amount):
      msgs.append(req(  'rd', i, addr[i], 0, 0 ))
      msgs.append(resp( 'rd', i, 1,       0, data[i] ))
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg, cacheSize = 4096 )

  #----------------------------------------------------------------------
  # Test Case: Read Hits: Test for entire line hits
  #----------------------------------------------------------------------

  def test_read_hit_cacheline( s ):
    base_addr = 0x20
    msgs = [
      req( 'in', 0x0, base_addr,    0, 0xdeadbeef ), resp( 'in', 0x0, 0, 0, 0          ),
      req( 'in', 0x1, base_addr+4,  0, 0xcafecafe ), resp( 'in', 0x1, 0, 0, 0          ),
      req( 'in', 0x2, base_addr+8,  0, 0xfafafafa ), resp( 'in', 0x2, 0, 0, 0          ),
      req( 'in', 0x3, base_addr+12, 0, 0xbabababa ), resp( 'in', 0x3, 0, 0, 0          ),
      req( 'rd', 0x4, base_addr,    0, 0          ), resp( 'rd', 0x4, 1, 0, 0xdeadbeef ),
      req( 'rd', 0x5, base_addr+4,  0, 0          ), resp( 'rd', 0x5, 1, 0, 0xcafecafe ),
      req( 'rd', 0x6, base_addr+8,  0, 0          ), resp( 'rd', 0x6, 1, 0, 0xfafafafa ),
      req( 'rd', 0x7, base_addr+12, 0, 0          ), resp( 'rd', 0x7, 1, 0, 0xbabababa ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg )

  #----------------------------------------------------------------------
  # Test Case: Write Hit: CLEAN
  #----------------------------------------------------------------------
  def test_write_hit_clean( s ):
    msgs = [
      #    type  opq  addr      len data                type  opq  test len data
      req( 'in', 0x0, 0x118c,    0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0  ),    
      req( 'wr', 0x1, 0x1184,    0, 55         ), resp( 'wr', 0x1, 1,   0,  0  ),
      req( 'rd', 0x2, 0x1184,    0, 0          ), resp( 'rd', 0x2, 1,   0,  55 ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg )
  #----------------------------------------------------------------------
  # Test Case: Write Hit: DIRTY
  #----------------------------------------------------------------------
  # The test field in the response message: 0 == MISS, 1 == HIT
  def test_write_hit_dirty( s ):
    msgs = [
      #    type  opq  addr      len data                type  opq  test len data
      req( 'in', 0x0, 0x66660,   0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
      req( 'wr', 0x1, 0x66660,   0, 0xffffffff ), resp( 'wr', 0x1, 1,   0,  0          ),
      req( 'wr', 0x2, 0x66664,   0, 0xc0ef     ), resp( 'wr', 0x2, 1,   0,  0 ),
      req( 'wr', 0x3, 0x66668,   0, 0x39287    ), resp( 'wr', 0x3, 1,   0,  0 ),
      req( 'wr', 0x4, 0x6666c,   0, 0xabcef    ), resp( 'wr', 0x4, 1,   0,  0 ),
      req( 'rd', 0x5, 0x66668,   0, 0          ), resp( 'rd', 0x5, 1,   0,  0x39287 ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg )
  #----------------------------------------------------------------------
  # Test Case: Write Hit: read/write hit 
  #----------------------------------------------------------------------
  # The test field in the response message: 0 == MISS, 1 == HIT
  def test_write_hits_read_hits( s ):
    msgs = [
      #    type  opq  addr                 len data                type  opq  test len data
      req( 'in', 0x0, 0, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
      req( 'rd', 0x1, 0, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0xdeadbeef ),
      req( 'wr', 0x2, 0, 0, 0xffffffff ), resp( 'wr', 0x2, 1,   0,  0          ),
      req( 'rd', 0x3, 0, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0xffffffff ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg )

  #----------------------------------------------------------------------
  # Test Case: Read Miss Clean:
  #----------------------------------------------------------------------
  def read_miss_1word_mem( s ):
    return [
      # addr                data
      0x00000000, 0xdeadbeef,
      0x00000004, 0x00c0ffee 
    ]
  def test_read_miss_1word_clean( s ):
    msgs = [
      #    type  opq  addr       len data                type  opq  test len data
      req( 'rd', 0x0, 0x00000000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0xdeadbeef ),
      req( 'rd', 0x1, 0x00000004, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0x00c0ffee )
    ]
    mem = s.read_miss_1word_mem()
    s.run_test( msgs, mem, CacheMsg, MemMsg )

  #----------------------------------------------------------------------
  # Test Case: Write Miss Clean:
  #----------------------------------------------------------------------
  def write_miss_1word_mem( s ):
    return [
      # addr                data
      0x00000000, 0xdeadbeef,
      0x00000004, 0x12345678,
      0x00000008, 0xeeeeeeee
    ]

  def test_write_miss_1word_clean( s ):
    msgs = [
      #    type  opq  addr       len data                type  opq test len data
      req( 'wr', 0x0, 0x00000000, 0, 0x00c0ffee ), resp( 'wr', 0x0, 0,   0, 0          ),
      req( 'rd', 0x1, 0x00000000, 0, 0          ), resp( 'rd', 0x1, 1,   0, 0x00c0ffee ),
      req( 'rd', 0x2, 0x00000008, 0, 0          ), resp( 'rd', 0x2, 1,   0, 0xeeeeeeee )
    ]
    mem = s.write_miss_1word_mem()
    s.run_test( msgs, mem, CacheMsg, MemMsg )

  def test_write_miss_offset( s ):
    msgs = [
      #    type  opq  addr       len data               type  opq  test len data
      req( 'wr', 0x0, 0x00000000, 0, 0xaeaeaeae), resp( 'wr', 0x0, 0,   0,  0         ), # write word 0x00000000
      req( 'wr', 0x1, 0x00000084, 0, 0x0e0e0e0e), resp( 'wr', 0x1, 0,   0,  0         ), # write word 0x00000080
      req( 'rd', 0x2, 0x00000000, 0, 0         ), resp( 'rd', 0x2, 1,   0,  0xaeaeaeae), # read  word 0x00000000
      req( 'rd', 0x3, 0x00000084, 0, 0         ), resp( 'rd', 0x3, 1,   0,  0x0e0e0e0e), # read  word 0x00000080
    ]
    mem = s.write_miss_1word_mem()
    s.run_test( msgs, mem, CacheMsg, MemMsg, cacheSize = 4096 )
  
  #-------------------------------------------------------------------------
  # Test cases: Read Dirty:
  #-------------------------------------------------------------------------

  def test_read_hit_1word_dirty( s ):
    msgs = [
      #    type  opq  addr      len data                type  opq  test len data
      req( 'in', 0x0, 0, 0, 0xdeadbeef ), resp( 'in', 0x0, 0, 0, 0          ),
      req( 'wr', 0x1, 0, 0, 0xbabababa ), resp( 'wr', 0x1, 1, 0, 0          ),
      req( 'rd', 0x2, 0, 0, 0          ), resp( 'rd', 0x2, 1, 0, 0xbabababa ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg )

  #-------------------------------------------------------------------------
  # Test cases: Write Dirty:
  #-------------------------------------------------------------------------

  def test_write_hit_1word_dirty( s ):
    msgs = [
      #    type  opq   addr      len data               type  opq   test len data
      req( 'in', 0x00, 0, 0, 0x0a0b0c0d ), resp('in', 0x00, 0,   0,  0          ), # write word  0x00000000
      req( 'wr', 0x01, 0, 0, 0xbeefbeeb ), resp('wr', 0x01, 1,   0,  0          ), # write word  0x00000000
      req( 'wr', 0x02, 0, 0, 0xc0ffeebb ), resp('wr', 0x02, 1,   0,  0          ), # write word  0x00000000
      req( 'rd', 0x03, 0, 0, 0          ), resp('rd', 0x03, 1,   0,  0xc0ffeebb ), # read  word  0x00000000
    ]
    mem = None
    s.run_test( msgs, mem, CacheMsg, MemMsg )

  #-------------------------------------------------------------------------
  # Test cases: Write Dirty:
  #-------------------------------------------------------------------------

  def test_read_miss_dirty( s ):
    msgs = [
      #    type  opq   addr                 len data               type  opq   test len data
      req( 'wr', 0x0, 0x00000000,  0, 0xbeefbeeb ), resp('wr', 0x0,   0,   0, 0          ), 
      req( 'rd', 0x1, 0x00010000,  0, 0          ), resp('rd', 0x1,   0,   0, 0x00c0ffee ), 
      req( 'rd', 0x2, 0x00000000,  0, 0          ), resp('rd', 0x2,   0,   0, 0xbeefbeeb ) 
    ]
    mem = [0x00010000, 0x00c0ffee]
    s.run_test( msgs, mem, CacheMsg, MemMsg )

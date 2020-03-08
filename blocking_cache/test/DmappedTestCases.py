"""
=========================================================================
 DmappedTestCases.py
=========================================================================
Direct mapped cache test cases

Author : Xiaoyu Yan, Eric Tang
Date   : 11 November 2019
"""

import pytest
import struct
import random
from pymtl3                    import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128 # cacheline bitwidth

CacheReqType, CacheRespType = mk_mem_msg(obw, abw, dbw)
MemReqType, MemRespType = mk_mem_msg(obw, abw, clw)

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return CacheReqType( type_, opaque, addr, len, data )

def resp( type_, opaque, test, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  return CacheRespType( type_, opaque, test, len, data )

class DmappedTestCases:
  def test_dmapped_read_hit_1word( s, dump_vcd, test_verilog ):
    msgs = [
        #    type  opq  addr     len data                type  opq  test len data
      req( 'in', 0x0, 0x000ab000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0, 0          ),
      req( 'rd', 0x1, 0x000ab000, 0, 0          ), resp( 'rd', 0x1, 1,   0, 0xdeadbeef ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  #----------------------------------------------------------------------
  # Test Case: Read Hits: path, many requests
  #----------------------------------------------------------------------
  def test_dmapped_read_hit_many( s, dump_vcd, test_verilog ):
    msgs = []
    for i in range(4):
      #                  type  opq  addr          len data
      msgs.append(req(  'in', i, ((0x00012000)<<2)+i*4, 0, i ))
      msgs.append(resp( 'in', i, 0,             0, 0 ))
    for i in range(4):
      msgs.append(req(  'rd', i, ((0x00012000)<<2)+i*4, 0, 0 ))
      msgs.append(resp( 'rd', i, 1,             0, i ))
    mem = None
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  #----------------------------------------------------------------------
  # Test Case: Read Hits: random requests
  #----------------------------------------------------------------------
  def test_dmapped_read_hit_random( s, dump_vcd, test_verilog ):
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
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,\
       cacheSize = 4096, dump_vcd=dump_vcd, test_verilog=test_verilog )

  #----------------------------------------------------------------------
  # Test Case: Read Hits: Test for entire line hits
  #----------------------------------------------------------------------

  def test_dmapped_read_hit_cacheline( s, dump_vcd, test_verilog ):
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
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  #----------------------------------------------------------------------
  # Test Case: Write Hit: CLEAN
  #----------------------------------------------------------------------
  def test_dmapped_write_hit_clean( s, dump_vcd, test_verilog, stall_prob=0, 
  latency=1, src_delay=0, sink_delay=0 ):
    msgs = [
      #    type  opq  addr      len data                type  opq  test len data
      req( 'in', 0x0, 0x118c,    0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0  ),
      req( 'wr', 0x1, 0x1184,    0, 55         ), resp( 'wr', 0x1, 1,   0,  0  ),
      req( 'rd', 0x2, 0x1184,    0, 0          ), resp( 'rd', 0x2, 1,   0,  55 ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
                1, 512, stall_prob, latency, src_delay, sink_delay,
                dump_vcd=dump_vcd, test_verilog=test_verilog )

  def test_dmapped_write_hit_clean_lat(s, dump_vcd, test_verilog):
    s.test_dmapped_write_hit_clean( dump_vcd, test_verilog, 0, 1, 7, 6 )

  #----------------------------------------------------------------------
  # Test Case: Write Hit: DIRTY
  #----------------------------------------------------------------------
  # The test field in the response message: 0 == MISS, 1 == HIT
  def test_dmapped_write_hit_dirty( s, dump_vcd, test_verilog ):
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
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)
  #----------------------------------------------------------------------
  # Test Case: Write Hit: read/write hit
  #----------------------------------------------------------------------
  # The test field in the response message: 0 == MISS, 1 == HIT
  def test_dmapped_write_hits_read_hits( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq  addr                 len data                type  opq  test len data
      req( 'in', 0x0, 0, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
      req( 'rd', 0x1, 0, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0xdeadbeef ),
      req( 'wr', 0x2, 0, 0, 0xffffffff ), resp( 'wr', 0x2, 1,   0,  0          ),
      req( 'rd', 0x3, 0, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0xffffffff ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  #----------------------------------------------------------------------
  # Test Case: Read Miss Clean:
  #----------------------------------------------------------------------
  def read_miss_1word_mem( s ):
    return [
      # addr                data
      0x00000000, 0xdeadbeef,
      0x00000004, 0x00c0ffee
    ]
  def test_dmapped_read_miss_1word_clean( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq  addr       len data                type  opq  test len data
      req( 'rd', 0x0, 0x00000000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0xdeadbeef ),
      req( 'rd', 0x1, 0x00000004, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0x00c0ffee )
    ]
    mem = s.read_miss_1word_mem()
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

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
  def test_dmapped_write_miss_1word_clean( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq  addr       len data                type  opq test len data
      req( 'wr', 0x0, 0x00000000, 0, 0x00c0ffee ), resp( 'wr', 0x0, 0,   0, 0          ),
      req( 'rd', 0x1, 0x00000000, 0, 0          ), resp( 'rd', 0x1, 1,   0, 0x00c0ffee ),
      req( 'rd', 0x2, 0x00000008, 0, 0          ), resp( 'rd', 0x2, 1,   0, 0xeeeeeeee )
    ]
    mem = s.write_miss_1word_mem()
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)


  def test_dmapped_write_miss_offset( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq  addr       len data               type  opq  test len data
      req( 'wr', 0x0, 0x00000000, 0, 0xaeaeaeae), resp( 'wr', 0x0, 0,   0,  0         ), # write word 0x00000000
      req( 'wr', 0x1, 0x00000084, 0, 0x0e0e0e0e), resp( 'wr', 0x1, 0,   0,  0         ), # write word 0x00000080
      req( 'rd', 0x2, 0x00000000, 0, 0         ), resp( 'rd', 0x2, 1,   0,  0xaeaeaeae), # read  word 0x00000000
      req( 'rd', 0x3, 0x00000084, 0, 0         ), resp( 'rd', 0x3, 1,   0,  0x0e0e0e0e), # read  word 0x00000080
    ]
    mem = s.write_miss_1word_mem()
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,\
       cacheSize = 4096, dump_vcd=dump_vcd, test_verilog=test_verilog )

  #-------------------------------------------------------------------------
  # Test cases: Read Dirty:
  #-------------------------------------------------------------------------

  def test_dmapped_read_hit_1word_dirty( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq  addr      len data                type  opq  test len data
      req( 'in', 0x0, 0, 0, 0xdeadbeef ), resp( 'in', 0x0, 0, 0, 0          ),
      req( 'wr', 0x1, 0, 0, 0xbabababa ), resp( 'wr', 0x1, 1, 0, 0          ),
      req( 'rd', 0x2, 0, 0, 0          ), resp( 'rd', 0x2, 1, 0, 0xbabababa ),
    ]
    mem = None
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  #-------------------------------------------------------------------------
  # Test cases: Write Dirty:
  #-------------------------------------------------------------------------

  def test_dmapped_write_hit_1word_dirty( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len data               type  opq   test len data
      req( 'in', 0x00, 0, 0, 0x0a0b0c0d ), resp('in', 0x00, 0,   0,  0          ), # write word  0x00000000
      req( 'wr', 0x01, 0, 0, 0xbeefbeeb ), resp('wr', 0x01, 1,   0,  0          ), # write word  0x00000000
      req( 'wr', 0x02, 0, 0, 0xc0ffeebb ), resp('wr', 0x02, 1,   0,  0          ), # write word  0x00000000
      req( 'rd', 0x03, 0, 0, 0          ), resp('rd', 0x03, 1,   0,  0xc0ffeebb ), # read  word  0x00000000
    ]
    mem = None
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  #-------------------------------------------------------------------------
  # Test cases: Write Dirty:
  #-------------------------------------------------------------------------

  def test_dmapped_read_miss_dirty( s, dump_vcd, test_verilog, stall_prob=0, 
  latency=1, src_delay=0, sink_delay=0 ):
    msgs = [
      #    type  opq   addr                 len data               type  opq   test len data
      req( 'wr', 0x0, 0x00000000,  0, 0xbeefbeeb ), resp('wr', 0x0,   0,   0, 0          ),
      req( 'rd', 0x1, 0x00010000,  0, 0          ), resp('rd', 0x1,   0,   0, 0x00c0ffee ),
      req( 'rd', 0x2, 0x00000000,  0, 0          ), resp('rd', 0x2,   0,   0, 0xbeefbeeb )
    ]
    mem = [0x00010000, 0x00c0ffee]
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
     1, 512, stall_prob, latency, src_delay, sink_delay, dump_vcd=dump_vcd, 
     test_verilog=test_verilog )

  def evict_mem( s ):
    return [
      # addr      # data (in int)
      0x00002000, 0x00facade,
      0x00002004, 0x05ca1ded,
      0x000a2000, 0x70facade,
      0x000a2004, 0x75ca1ded,
    ]
  #-------------------------------------------------------------------------
  # Test Case: Direct Mapped Read Evict
  #-------------------------------------------------------------------------
  def test_dmapped_read_evict_1word( s, dump_vcd, test_verilog, stall_prob=0, 
  latency=1, src_delay=0, sink_delay=0 ):
    msgs = [
        #    type  opq   addr      len  data               type  opq test len  data
      req( 'wr', 0x00, 0x00002000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), # write something
      req( 'rd', 0x01, 0x000a2000, 0, 0         ), resp( 'rd', 0x01, 0, 0, 0x70facade ), # read miss on dirty line
      req( 'rd', 0x02, 0x00002000, 0, 0         ), resp( 'rd', 0x02, 0, 0, 0xffffff00 ), # read evicted address
    ]
    mem = s.evict_mem()
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
                1, 512, stall_prob, latency, src_delay, sink_delay,
                dump_vcd=dump_vcd, test_verilog=test_verilog )

  def evict_mem( s ):
    return [
      # addr      # data (in int)
      0x00002000, 0x00facade,
      0x00002004, 0x05ca1ded,
      0x000a2000, 0x70facade,
      0x000a2004, 0x75ca1ded,
    ]

  #-------------------------------------------------------------------------
  # Test Case: Direct Mapped Write Evict
  #-------------------------------------------------------------------------
  # Test cases designed for direct-mapped cache where we evict a cache line
  def test_dmapped_write_evict_1word( s, dump_vcd, test_verilog, stall_prob=0,
   latency=1, src_delay=0, sink_delay=0 ):
    msgs = [
      #    type  opq   addr      len  data               type  opq test len  data
      req( 'wr', 0x00, 0x00002000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), #refill-write
      req( 'wr', 0x02, 0x000a2000, 0, 0x8932    ), resp( 'wr', 0x02, 0, 0, 0 ),          #evict
      req( 'rd', 0x03, 0x000a2000, 0, 0         ), resp( 'rd', 0x03, 1, 0, 0x8932 ),     #read new written data
      req( 'rd', 0x04, 0x00002000, 0, 0         ), resp( 'rd', 0x04, 0, 0, 0xffffff00 ), #read-evicted data
    ]
    mem = s.evict_mem()
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
     512, stall_prob, latency, src_delay, sink_delay, dump_vcd=dump_vcd, 
     test_verilog=test_verilog )

  #-------------------------------------------------------------------------
  # Test Case: test direct-mapped
  #-------------------------------------------------------------------------
  # Test cases designed for direct-mapped cache

  def dir_mapped_long0_mem( s ):
    return [
      # addr      # data (in int)
      0x00002000, 0x00facade,
      0x00002004, 0x05ca1ded,
      0x00002070, 0x70facade,
      0x00002074, 0x75ca1ded,
    ]
  def test_dmapped_long0_msg( s, dump_vcd, test_verilog, stall_prob=0, latency=1, 
  src_delay=0, sink_delay=0 ):
    msgs = [
      #    type  opq   addr      len  data               type  opq test len  data
      req( 'wr', 0x00, 0x00000000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), # Write to cacheline 0
      req( 'wr', 0x01, 0x00000004, 0, 0xffffff01), resp( 'wr', 0x01, 1, 0, 0          ),
      req( 'wr', 0x02, 0x00000008, 0, 0xffffff02), resp( 'wr', 0x02, 1, 0, 0          ),
      req( 'wr', 0x03, 0x0000000c, 0, 0xffffff03), resp( 'wr', 0x03, 1, 0, 0          ),
      req( 'wr', 0x04, 0x00001000, 0, 0xffffff04), resp( 'wr', 0x04, 0, 0, 0          ), # Write to cacheline 0
      req( 'wr', 0x05, 0x00001004, 0, 0xffffff05), resp( 'wr', 0x05, 1, 0, 0          ),
      req( 'wr', 0x06, 0x00001008, 0, 0xffffff06), resp( 'wr', 0x06, 1, 0, 0          ),
      req( 'wr', 0x07, 0x0000100c, 0, 0xffffff07), resp( 'wr', 0x07, 1, 0, 0          ),
      req( 'rd', 0x08, 0x00002000, 0, 0         ), resp( 'rd', 0x08, 0, 0, 0x00facade ), # Evict cache 0
      req( 'rd', 0x09, 0x00002004, 0, 0         ), resp( 'rd', 0x09, 1, 0, 0x05ca1ded ), # Read again from same cacheline
      req( 'rd', 0x0a, 0x00001004, 0, 0         ), resp( 'rd', 0x0a, 0, 0, 0xffffff05 ), # Read from cacheline 0
      req( 'wr', 0x0b, 0x0000100c, 0, 0xffffff09), resp( 'wr', 0x0b, 1, 0, 0          ), # Write to cacheline 0
      req( 'rd', 0x0c, 0x0000100c, 0, 0         ), resp( 'rd', 0x0c, 1, 0, 0xffffff09 ), # Read that back
      req( 'rd', 0x0d, 0x00000000, 0, 0         ), resp( 'rd', 0x0d, 0, 0, 0xffffff00 ), # Evict cacheline 0
      req( 'wr', 0x10, 0x00000070, 0, 0xffffff00), resp( 'wr', 0x10, 0, 0, 0          ), # Write to cacheline 7
      req( 'wr', 0x11, 0x00000074, 0, 0xffffff01), resp( 'wr', 0x11, 1, 0, 0          ),
      req( 'wr', 0x12, 0x00000078, 0, 0xffffff02), resp( 'wr', 0x12, 1, 0, 0          ),
      req( 'wr', 0x13, 0x0000007c, 0, 0xffffff03), resp( 'wr', 0x13, 1, 0, 0          ),
      req( 'wr', 0x14, 0x00001070, 0, 0xffffff04), resp( 'wr', 0x14, 0, 0, 0          ), # Write to cacheline 7
      req( 'wr', 0x15, 0x00001074, 0, 0xffffff05), resp( 'wr', 0x15, 1, 0, 0          ),
      req( 'wr', 0x16, 0x00001078, 0, 0xffffff06), resp( 'wr', 0x16, 1, 0, 0          ),
      req( 'wr', 0x17, 0x0000107c, 0, 0xffffff07), resp( 'wr', 0x17, 1, 0, 0          ),
      req( 'rd', 0x18, 0x00002070, 0, 0         ), resp( 'rd', 0x18, 0, 0, 0x70facade ), # Evict cacheline 7
      req( 'rd', 0x19, 0x00002074, 0, 0         ), resp( 'rd', 0x19, 1, 0, 0x75ca1ded ), # Read again from same cacheline
      req( 'rd', 0x1a, 0x00001074, 0, 0         ), resp( 'rd', 0x1a, 0, 0, 0xffffff05 ), # Read from cacheline 7
      req( 'wr', 0x1b, 0x0000107c, 0, 0xffffff09), resp( 'wr', 0x1b, 1, 0, 0          ), # Write to cacheline 7
      req( 'rd', 0x1c, 0x0000107c, 0, 0         ), resp( 'rd', 0x1c, 1, 0, 0xffffff09 ), # Read that back
      req( 'rd', 0x1d, 0x00000070, 0, 0         ), resp( 'rd', 0x1d, 0, 0, 0xffffff00 ), # Evict cacheline 0 again
    ]
    mem = s.dir_mapped_long0_mem()
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
                1, 512, stall_prob, latency, src_delay, sink_delay,
                dump_vcd=dump_vcd, test_verilog=test_verilog )


  def test_dmapped_1byte_read_hit( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data                type  opq test len  data
      req( 'in', 0x00, 0x00000000, 0, 0xabcdef12), resp( 'in', 0x00, 0, 0, 0 ),
      req( 'rd', 0x01, 0x00000000, 1, 0), resp( 'rd', 0x01, 1, 1, 0x00000012          ),
      req( 'rd', 0x02, 0x00000001, 1, 0), resp( 'rd', 0x02, 1, 1, 0x000000ef          ),
      req( 'rd', 0x03, 0x00000002, 1, 0), resp( 'rd', 0x03, 1, 1, 0x000000cd          ),
      req( 'rd', 0x04, 0x00000003, 1, 0), resp( 'rd', 0x04, 1, 1, 0x000000ab          ),
    ]
    mem = None
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_1byte_write_hit( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data                type  opq test len  data
      req( 'in', 0x00, 0x00000000, 0, 0xabcdef12), resp( 'in', 0x00, 0, 0, 0          ),
      req( 'wr', 0x01, 0x00000000, 1, 0x99),       resp( 'wr', 0x01, 1, 1, 0          ),
      req( 'wr', 0x01, 0x00000001, 1, 0x66),       resp( 'wr', 0x01, 1, 1, 0          ),
      req( 'wr', 0x01, 0x00000002, 1, 0x33),       resp( 'wr', 0x01, 1, 1, 0          ),
      req( 'wr', 0x01, 0x00000003, 1, 0x11),       resp( 'wr', 0x01, 1, 1, 0          ),
      req( 'rd', 0x02, 0x00000000, 0, 0),          resp( 'rd', 0x02, 1, 0, 0x11336699 ),
    ]
    mem = None
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def dir_mapped_subword_mem( s ):
    return [
      # addr      # data (in int)
      0x00000000, 0x00facade,
      0x00001000, 0x01234567,
      0x00002000, 0x05ca1ded,
      0x00003000, 0xdeadbeef,
      0x00000100, 0x70facade,
      0x00002100, 0x75ca1ded,
    ]

  def test_dmapped_1byte_read_miss( s, dump_vcd, test_verilog ):

    msgs = [
      #    type  opq   addr      len  data      type  opq test len  data    ),
      req( 'rd', 0x00, 0x00000000, 1, 0), resp( 'rd', 0x00, 0, 1, 0xde ),
      req( 'rd', 0x01, 0x00001001, 1, 0), resp( 'rd', 0x01, 0, 1, 0x45 ),
      req( 'rd', 0x02, 0x00002002, 1, 0), resp( 'rd', 0x02, 0, 1, 0xca ),
      req( 'rd', 0x03, 0x00003003, 1, 0), resp( 'rd', 0x03, 0, 1, 0xde ),
    ]
    mem = s.dir_mapped_subword_mem()
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_1byte_write_miss( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data                type  opq test len  data
      req( 'wr', 0x00, 0x00000000, 1, 0x11), resp( 'wr', 0x00, 0, 1, 0          ),
      req( 'wr', 0x01, 0x00001001, 1, 0x22), resp( 'wr', 0x01, 0, 1, 0          ),
      req( 'wr', 0x02, 0x00002002, 1, 0x33), resp( 'wr', 0x02, 0, 1, 0 ),
      req( 'wr', 0x03, 0x00003003, 1, 0x44), resp( 'wr', 0x03, 0, 1, 0 ),
      req( 'rd', 0x00, 0x00000000, 0, 0), resp( 'rd', 0x00, 0, 0, 0x00faca11 ),
      req( 'rd', 0x01, 0x00001000, 0, 0), resp( 'rd', 0x01, 0, 0, 0x01232267 ),
      req( 'rd', 0x02, 0x00002000, 0, 0), resp( 'rd', 0x02, 0, 0, 0x05331ded ),
      req( 'rd', 0x03, 0x00003000, 0, 0), resp( 'rd', 0x03, 0, 0, 0x44adbeef ),
    ]
    mem = s.dir_mapped_subword_mem()
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_halfword_read_hit( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data                type  opq test len  data
      req( 'in', 0x00, 0x00000000, 0, 0xabcdef12), resp( 'in', 0x00, 0, 0, 0          ),
      req( 'rd', 0x01, 0x00000000, 2, 0),          resp( 'rd', 0x01, 1, 2, 0x0000ef12 ),
      req( 'rd', 0x02, 0x00000002, 2, 0),          resp( 'rd', 0x02, 1, 2, 0x0000abcd ),
      ]
    mem = None
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_halfword_write_hit( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data                type  opq test len  data
      req( 'in', 0x00, 0x00000000, 0, 0xabcdef12), resp( 'in', 0x00, 0, 0, 0          ),
      req( 'wr', 0x01, 0x00000000, 2, 0x99),       resp( 'wr', 0x01, 1, 2, 0          ),
      req( 'wr', 0x01, 0x00000002, 2, 0xac13),     resp( 'wr', 0x01, 1, 2, 0          ),
      req( 'rd', 0x02, 0x00000000, 0, 0),          resp( 'rd', 0x02, 1, 0, 0xac130099 ),
    ]
    mem = None
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_halfword_read_miss( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data      type  opq test len  data    ),
      req( 'rd', 0x00, 0x00000000, 2, 0), resp( 'rd', 0x00, 0, 2, 0xcade ),
      req( 'rd', 0x02, 0x00002002, 2, 0), resp( 'rd', 0x02, 0, 2, 0x05ca ),
    ]
    mem = s.dir_mapped_subword_mem()
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_halfword_write_miss( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data                type  opq test len  data
      req( 'wr', 0x00, 0x00000000, 2, 0x11), resp( 'wr', 0x00, 0, 2, 0          ),
      req( 'wr', 0x02, 0x00002002, 2, 0x33), resp( 'wr', 0x02, 0, 2, 0 ),
      req( 'rd', 0x00, 0x00000000, 0, 0), resp( 'rd', 0x00, 0, 0, 0x00fa0011 ),
      req( 'rd', 0x02, 0x00002000, 0, 0), resp( 'rd', 0x02, 0, 0, 0x00331ded ),
    ]
    mem = s.dir_mapped_subword_mem()
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def hypo_mem( s ):
    return [
      0x00000000, 0xa0b0c0d0,
      0x00000004, 0xc0ffee88,
      0x00000008, 0x12345678,
      0x0000000c, 0xdeadbeef,
    ]

  def test_dmapped_hypo1( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data      type  opq test len  data
      req( 'rd', 0x04, 0x00000006, 1, 0), resp( 'rd', 0x04, 0, 1, 0x000000ff          ),
      req( 'rd', 0x04, 0x00000007, 1, 0), resp( 'rd', 0x04, 1, 1, 0x000000c0          ),
    ]
    mem = s.hypo_mem()
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_hypo2( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr      len  data      type  opq test len  data
      req( 'rd', 0x04, 0x00000006, 2, 0), resp( 'rd', 0x04, 0, 2, 0x0000c0ff          ),
      req( 'rd', 0x04, 0x00000004, 2, 0), resp( 'rd', 0x04, 1, 2, 0x0000ee88          ),
    ]
    mem = s.hypo_mem()
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
    dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_read_evict_1word_lat( s, dump_vcd, test_verilog ):
    s.test_dmapped_read_evict_1word( dump_vcd, test_verilog, 5, 5, 5, 5 )

  def test_dmapped_write_evict_1word_lat( s, dump_vcd, test_verilog ):
    s.test_dmapped_write_evict_1word( dump_vcd, test_verilog, 5, 5, 5, 5 )

  def test_dmapped_long0_msg_lat( s, dump_vcd, test_verilog ):
    s.test_dmapped_long0_msg( dump_vcd, test_verilog, 5, 5, 5, 5 )

  def test_hypo_lat1( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr    len  data     type  opq test len  data
      req( 'rd', 0, 0x00000000, 0, 0), resp( 'rd', 0x0, 0, 0, 0xa0b0c0d0          ),
      req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 0x1, 1, 0, 0xa0b0c0d0          ),
    ]
    mem = s.hypo_mem()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 64)
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
               1, 128, 0, 1, 0, 1, dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_proc_cache( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr    len  data     type  opq test len  data
      req( 'wr', 0, 0x00002000, 0, 0xdeadbeef), resp( 'wr', 0x0, 0, 0, 0          ),
      req( 'rd', 1, 0x00002000, 0, 0), resp( 'rd', 0x1, 1, 0, 0xdeadbeef          ),
    ]
    mem = s.hypo_mem()
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
               1, 4096, 0, 1, 7, 6, dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_verilog1( s, dump_vcd, test_verilog ):
    msgs = [
      #    type  opq   addr    len  data     type  opq test len  data
      req( 'rd', 0, 0x00000000, 0, 0), resp( 'rd', 0x0, 0, 0, 0xa0b0c0d0          ),
      req( 'rd', 1, 0x00000000, 0, 0), resp( 'rd', 0x1, 1, 0, 0xa0b0c0d0          ),
      req( 'rd', 2, 0x00000000, 0, 0), resp( 'rd', 0x2, 1, 0, 0xa0b0c0d0          ),
    ]
    mem = s.hypo_mem()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 64)
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
               1, 128, 0, 1, 0, 0, dump_vcd=dump_vcd, test_verilog=test_verilog)

  def test_dmapped_verilog2( s, dump_vcd, test_verilog ):
    msgs = []
    for i in range(4):
      #                  type  opq  addr          len data
      msgs.append(req(  'in', i, ((0x00012000)<<2)+i*4, 0, i ))
      msgs.append(resp( 'in', i, 0,             0, 0 ))
    for i in range(4):
      msgs.append(req(  'rd', i, ((0x00012000)<<2)+i*4, 0, 0 ))
      msgs.append(resp( 'rd', i, 1,             0, i ))
    mem = None
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 64)
    s.run_test(msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType,
               1, 128, 0, 1, 0, 0, dump_vcd=dump_vcd, test_verilog=test_verilog)

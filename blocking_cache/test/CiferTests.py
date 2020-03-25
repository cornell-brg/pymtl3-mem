"""
=========================================================================
 CiferTests.py
=========================================================================
Direct mapped cache test cases

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 11 November 2019
"""

import random
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from pymtl3.stdlib.ifcs.MemMsg import mk_mem_msg as mk_cache_msg
# cifer specific memory req/resp msg
from mem_pclib.ifcs.MemMsg     import mk_mem_msg 
from mem_pclib.constants.constants import *

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128 # cacheline bitwidth

CacheReqType, CacheRespType = mk_cache_msg(obw, abw, dbw)
MemReqType, MemRespType = mk_mem_msg(obw, abw, clw)

#-------------------------------------------------------------------------
# make messages
#-------------------------------------------------------------------------

def req( type_, opaque, addr, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  elif type_ == 'ad': type_ = MemMsgType.AMO_ADD
  return CacheReqType( type_, opaque, addr, len, data )

def resp( type_, opaque, test, len, data ):
  if   type_ == 'rd': type_ = MemMsgType.READ
  elif type_ == 'wr': type_ = MemMsgType.WRITE
  elif type_ == 'in': type_ = MemMsgType.WRITE_INIT
  elif type_ == 'ad': type_ = MemMsgType.AMO_ADD
  return CacheRespType( type_, opaque, test, len, data )

class CiferTests:
  
  def cifer_test_memory( s ):
    return [
      0x00000000, 1,
      0x00000004, 2,
      0x00000008, 3,
      0x0000000c, 4,
      0x00020000, 5,
      0x00020004, 5,
      0x00020008, 5,
      0x0002000c, 5,
      0x0000005c, 6,
      0x00000060, 7,
    ]
  
  def test_cifer_dmapped_write_hit_clean( s, dump_vcd, test_verilog, stall_prob=0,
   latency=1, src_delay=0, sink_delay=0 ):
    msgs = [
        #    type  opq   addr      len  data       type  opq test len  data
        req( 'rd', 0x00, 0x00000000, 0, 0),   resp( 'rd', 0x00, 0, 0, 1          ), #refill-write
        req( 'wr', 0x01, 0x00000000, 0, 0xf), resp( 'wr', 0x01, 1, 0, 0 ),          #evict
        req( 'wr', 0x02, 0x00000004, 0, 0xe), resp( 'wr', 0x02, 1, 0, 0 ),     #read new written data
        req( 'wr', 0x03, 0x00000008, 0, 0xc), resp( 'wr', 0x03, 1, 0, 0 ), #read-evicted data
        req( 'wr', 0x04, 0x0000000c, 0, 0xb), resp( 'wr', 0x04, 1, 0, 0 ), #read-evicted data
        req( 'wr', 0x05, 0x00000000, 0, 0xa), resp( 'wr', 0x05, 1, 0, 0 ), #read-evicted data
      ]
    mem = s.cifer_test_memory()
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
    32, stall_prob, latency, src_delay, sink_delay, dump_vcd=dump_vcd, 
    test_verilog=test_verilog )

  def test_cifer_hypo1( s, dump_vcd, test_verilog, stall_prob=0, latency=1, \
    src_delay=0, sink_delay=0 ):
    msgs = [
        #    type  opq   addr      len  data       type  opq test len  data
        req( 'wr', 0x00, 0x0000005c, 0, 0xfff), resp( 'wr', 0x00, 0, 0, 0 ), #refill-write
        req( 'rd', 0x01, 0x00000008, 0, 0), resp( 'rd', 0x01, 0, 0, 3 ),     #evict
        req( 'rd', 0x02, 0x00000060, 0, 0), resp( 'rd', 0x02, 0, 0, 7 ),     #read new written data
      ]
    mem = s.cifer_test_memory()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 64)
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
    16, stall_prob, latency, src_delay, sink_delay, dump_vcd=dump_vcd, 
    test_verilog=test_verilog )
  
  def test_cifer_amo( s, dump_vcd, test_verilog, stall_prob=0, latency=1, \
    src_delay=0, sink_delay=0 ):
    msgs = [
        #    type  opq   addr   len  data     type  opq test len  data
        req( 'ad', 0x00, 0x00000, 0, 0), resp( 'ad', 0x00, 0, 0, 1 ),   
      ]
    mem = s.cifer_test_memory()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 64)
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
    16, stall_prob, latency, src_delay, sink_delay, dump_vcd=dump_vcd, 
    test_verilog=test_verilog )
  
  def test_cifer_amo_dirty( s, dump_vcd, test_verilog, stall_prob=0, latency=1, \
    src_delay=0, sink_delay=0 ):
    msgs = [
        #    type  opq   addr       len data         type  opq test len  data
        req( 'wr', 0x00, 0x00000008, 0, 0xff), resp( 'wr', 0x00, 0,  0,  0    ),          
        req( 'ad', 0x01, 0x00000008, 0, 0x11), resp( 'ad', 0x01, 0,  0,  0x11 ),  
    ]
    mem = s.cifer_test_memory()
    MemReqType, MemRespType = mk_mem_msg(obw, abw, 64)
    s.run_test( msgs, mem, CacheReqType, CacheRespType, MemReqType, MemRespType, 1,
    16, stall_prob, latency, src_delay, sink_delay, dump_vcd=dump_vcd, 
    test_verilog=test_verilog )

"""
=========================================================================
 CiferTests.py
=========================================================================
Direct mapped cache test cases

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 11 November 2019
"""

import pytest
import struct
import random
from pymtl3                    import *
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from pymtl3.stdlib.ifcs.MemMsg import mk_mem_msg as mk_cache_msg
# cifer specific memory req/resp msg
from mem_pclib.ifcs.MemMsg     import mk_mem_msg 

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128 # cacheline bitwidth

CacheReqType, CacheRespType = mk_cache_msg(obw, abw, dbw)
MemReqType, MemRespType = mk_cache_msg(obw, abw, clw)

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
    64, stall_prob, latency, src_delay, sink_delay, dump_vcd=dump_vcd, 
    test_verilog=test_verilog )

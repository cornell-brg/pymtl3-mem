"""
=========================================================================
 DmappedTestCases.py
=========================================================================
Direct mapped cache test cases

Author : Xiaoyu Yan, Eric Tang
Date   : 17 November 2019
"""

import pytest
import struct
import random
from pymtl3.stdlib.test.test_utils import mk_test_case_table
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128
CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
MemMsg = ReqRespMsgTypes(obw, abw, clw)

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

#-------------------------------------------------------------------------
# Test Case: Direct Mapped Read Evict 
#-------------------------------------------------------------------------
# Test case designed for direct-mapped cache where a cache line must be evicted
def read_evict( base_addr ):
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    req( 'wr', 0x00, 0x00002000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), # write something
    req( 'rd', 0x01, 0x00002000, 0, 0         ), resp( 'rd', 0x01, 1, 0, 0xffffff00 ), # read to make sure write happened
    req( 'rd', 0x02, 0x000a2000, 0, 0         ), resp( 'rd', 0x02, 0, 0, 0x70facade ), # read miss on dirty line
    req( 'rd', 0x03, 0x00002000, 0, 0         ), resp( 'rd', 0x03, 0, 0, 0xffffff00 ), # read evicted address
  ]

def evict_mem( base_addr ):
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
def write_evict( base_addr ):
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    req( 'wr', 0x00, 0x00002000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), #refill-write
    req( 'rd', 0x01, 0x00002000, 0, 0         ), resp( 'rd', 0x01, 1, 0, 0xffffff00 ), #read written data
    req( 'wr', 0x02, 0x000a2000, 0, 0x8932    ), resp( 'wr', 0x02, 0, 0, 0 ),          #evict
    req( 'rd', 0x03, 0x000a2000, 0, 0         ), resp( 'rd', 0x03, 1, 0, 0x8932 ),     #read new written data
    req( 'rd', 0x04, 0x00002000, 0, 0         ), resp( 'rd', 0x04, 0, 0, 0xffffff00 ), #read-evicted data
  ]

#-------------------------------------------------------------------------
# Test Case: test direct-mapped
#-------------------------------------------------------------------------
# Test cases designed for direct-mapped cache

def dir_mapped_long0_msg( base_addr ):
  return [
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

def dir_mapped_long0_mem( base_addr ):
  return [
    # addr      # data (in int)
    0x00002000, 0x00facade,
    0x00002004, 0x05ca1ded,
    0x00002070, 0x70facade,
    0x00002074, 0x75ca1ded,
  ]

#---------------------------------------------------------------------------------------------
# Test table for direct mapped cache tests
#---------------------------------------------------------------------------------------------

test_case_table_dmap = mk_test_case_table([
  ( "                        msg_func               mem_data_func         stall lat src sink"),
  [ "read_evict",            read_evict,            evict_mem,            0.0,  1,  0,  0    ],
  [ "write_evict",           write_evict,           evict_mem,            0.0,  1,  0,  0    ],
  [ "dir_mapped_long0_msg",  dir_mapped_long0_msg,  dir_mapped_long0_mem, 0.0,  1,  0,  0    ],
  [ "dmap_stall",            dir_mapped_long0_msg,  dir_mapped_long0_mem, 1.0,  5,  0,  0    ],
])


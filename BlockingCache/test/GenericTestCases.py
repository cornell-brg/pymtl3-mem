"""
=========================================================================
 GenericTestCases.py
=========================================================================
Cache type independent test cases for cache of any associativity

Author : Xiaoyu Yan, Eric Tang
Date   : 04 November 2019
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

#----------------------------------------------------------------------
# Test Case: Read Hits: 
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def read_hit_1word_clean( base_addr=0x0 ):
  return [
    #    type  opq  addr                 len data                type  opq  test len data
    req( 'in', 0x0, base_addr+0x000ab000, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'rd', 0x1, base_addr+0x000ab000, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0xdeadbeef ),
  ]

#----------------------------------------------------------------------
# Test Case: Read Hits: path, many requests
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def read_hit_many_clean( base_addr=0x0 ):
  array = []
  for i in range(4):
    #                  type  opq  addr          len data
    array.append(req(  'in', i, ((base_addr+0x00012000)<<2)+i*4, 0, i ))
    array.append(resp( 'in', i, 0,             0, 0 ))
  for i in range(4):
    array.append(req(  'rd', i, ((base_addr+0x00012000)<<2)+i*4, 0, 0 ))
    array.append(resp( 'rd', i, 1,             0, i ))
  return array

#----------------------------------------------------------------------
# Test Case: Read Hits: random requests
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def read_hit_random_clean( base_addr=0x0 ):
  array = []
  test_amount = 4
  random.seed(1)
  addr = [(base_addr + random.randint(0,0x00fff)) << 2 for i in range(test_amount)]
  data = [random.randint(0,0xfffff) for i in range(test_amount)]
  for i in range(test_amount):
    #                  type  opq  addr     len data
    array.append(req(  'in', i,   addr[i], 0,  data[i]))
    #                  type  opq  test     len data
    array.append(resp( 'in', i,   0,       0,  0 ))
  for i in range(test_amount):
    array.append(req(  'rd', i, addr[i], 0, 0 ))
    array.append(resp( 'rd', i, 1,       0, data[i] ))
  return array

#----------------------------------------------------------------------
# Test Case: Read Hits: Test for entire line hits
#----------------------------------------------------------------------

def read_hit_1line_clean( base_addr ):
  return [
    req( 'in', 0x0, base_addr,    0, 0xdeadbeef ), resp( 'in', 0x0, 0, 0, 0          ),
    req( 'in', 0x1, base_addr+4,  0, 0xcafecafe ), resp( 'in', 0x1, 0, 0, 0          ),
    req( 'in', 0x2, base_addr+8,  0, 0xfafafafa ), resp( 'in', 0x2, 0, 0, 0          ),
    req( 'in', 0x3, base_addr+12, 0, 0xbabababa ), resp( 'in', 0x3, 0, 0, 0          ),
    req( 'rd', 0x4, base_addr,    0, 0          ), resp( 'rd', 0x4, 1, 0, 0xdeadbeef ),
    req( 'rd', 0x5, base_addr+4,  0, 0          ), resp( 'rd', 0x5, 1, 0, 0xcafecafe ),
    req( 'rd', 0x6, base_addr+8,  0, 0          ), resp( 'rd', 0x6, 1, 0, 0xfafafafa ),
    req( 'rd', 0x7, base_addr+12, 0, 0          ), resp( 'rd', 0x7, 1, 0, 0xbabababa ),
  ]

#----------------------------------------------------------------------
# Test Case: Write Hit: CLEAN
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def write_hit_clean( base_addr=0x0 ):
  return [
    #    type  opq  addr      len data                type  opq  test len data
    req( 'in', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'wr', 0x1, base_addr, 0, 0xffffffff ), resp( 'wr', 0x1, 1,   0,  0          ),
    req( 'rd', 0x2, base_addr, 0, 0          ), resp( 'rd', 0x2, 1,   0,  0xffffffff ),
    req( 'in', 0x3, 0x118c,    0, 0xdeadbeef ), resp( 'in', 0x3, 0,   0,  0          ),    
    req( 'wr', 0x4, 0x1184,    0, 55         ), resp( 'wr', 0x4, 1,   0,  0 ),
    req( 'rd', 0x5, 0x1184,    0, 0          ), resp( 'rd', 0x5, 1,   0,  55 ),
  ]
#----------------------------------------------------------------------
# Test Case: Write Hit: DIRTY
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def write_hit_dirty( base_addr=0x0 ):
  return [
    #    type  opq  addr      len data                type  opq  test len data
    req( 'in', 0x0, 0x66660,   0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'wr', 0x1, 0x66660,   0, 0xffffffff ), resp( 'wr', 0x1, 1,   0,  0          ),
    req( 'wr', 0x2, 0x66664,   0, 0xc0ef     ), resp( 'wr', 0x2, 1,   0,  0 ),
    req( 'wr', 0x3, 0x66668,   0, 0x39287    ), resp( 'wr', 0x3, 1,   0,  0 ),
    req( 'wr', 0x4, 0x6666c,   0, 0xabcef    ), resp( 'wr', 0x4, 1,   0,  0 ),
    req( 'rd', 0x5, 0x66668,   0, 0          ), resp( 'rd', 0x5, 1,   0,  0x39287 ),
  ]
#----------------------------------------------------------------------
# Test Case: Write Hit: read/write hit 
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def write_hits_read_hits( base_addr=0x0 ):
  return [
    #    type  opq  addr                 len data                type  opq  test len data
    req( 'in', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'in', 0x0, 0,   0,  0          ),
    req( 'rd', 0x1, base_addr, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0xdeadbeef ),
    req( 'wr', 0x2, base_addr, 0, 0xffffffff ), resp( 'wr', 0x2, 1,   0,  0          ),
    req( 'rd', 0x3, base_addr, 0, 0          ), resp( 'rd', 0x3, 1,   0,  0xffffffff ),
  ]

#----------------------------------------------------------------------
# Test Case: Read Miss Clean:
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def read_miss_1word_clean( base_addr=0x0 ):
  return [
    #    type  opq  addr                 len data                type  opq  test len data
    req( 'rd', 0x0, base_addr+0x00000000, 0, 0          ), resp( 'rd', 0x0, 0,   0,  0xdeadbeef ),
    req( 'rd', 0x1, base_addr+0x00000004, 0, 0          ), resp( 'rd', 0x1, 1,   0,  0x00c0ffee )
  ]

def read_miss_1word_mem( base_addr=0x0 ):
  return [
    # addr                data
    base_addr+0x00000000, 0xdeadbeef,
    base_addr+0x00000004, 0x00c0ffee 
  ]

#----------------------------------------------------------------------
# Test Case: Write Miss Clean:
#----------------------------------------------------------------------
# The test field in the response message: 0 == MISS, 1 == HIT
def write_miss_1word_clean( base_addr=0x0 ):
  return [
    #    type  opq  addr                 len data                type  opq test len data
    req( 'wr', 0x0, base_addr+0x00000000, 0, 0x00c0ffee ), resp( 'wr', 0x0, 0,   0, 0          ),
    req( 'rd', 0x1, base_addr+0x00000000, 0, 0          ), resp( 'rd', 0x1, 1,   0, 0x00c0ffee ),
    req( 'rd', 0x2, base_addr+0x00000008, 0, 0          ), resp( 'rd', 0x2, 1,   0, 0xeeeeeeee )
  ]

def write_miss_1word_mem( base_addr=0x0 ):
  return [
    # addr                data
    base_addr+0x00000000, 0xdeadbeef,
    base_addr+0x00000004, 0x12345678,
    base_addr+0x00000008, 0xeeeeeeee
  ]

def write_miss_offset( base_addr ):
  return [
    #    type  opq  addr       len data               type  opq  test len data
    req( 'wr', 0x0, 0x00000000, 0, 0xaeaeaeae), resp( 'wr', 0x0, 0,   0,  0         ), # write word 0x00000000
    req( 'wr', 0x1, 0x00000084, 0, 0x0e0e0e0e), resp( 'wr', 0x1, 0,   0,  0         ), # write word 0x00000080
    req( 'rd', 0x2, 0x00000000, 0, 0         ), resp( 'rd', 0x2, 1,   0,  0xaeaeaeae), # read  word 0x00000000
    req( 'rd', 0x3, 0x00000084, 0, 0         ), resp( 'rd', 0x3, 1,   0,  0x0e0e0e0e), # read  word 0x00000080
  ]
  
#-------------------------------------------------------------------------
# Test cases: Read Dirty:
#-------------------------------------------------------------------------

def read_hit_1word_dirty( base_addr ):
  return [
    #    type  opq  addr      len data                type  opq  test len data
    req( 'in', 0x0, base_addr, 0, 0xdeadbeef ), resp( 'in', 0x0, 0, 0, 0          ),
    req( 'wr', 0x1, base_addr, 0, 0xbabababa ), resp( 'wr', 0x1, 1, 0, 0          ),
    req( 'rd', 0x2, base_addr, 0, 0          ), resp( 'rd', 0x2, 1, 0, 0xbabababa ),
  ]

#-------------------------------------------------------------------------
# Test cases: Write Dirty:
#-------------------------------------------------------------------------

def write_hit_1word_dirty( base_addr ):
  return [
    #    type  opq   addr      len data               type  opq   test len data
    req( 'in', 0x00, base_addr, 0, 0x0a0b0c0d ), resp('in', 0x00, 0,   0,  0          ), # write word  0x00000000
    req( 'wr', 0x01, base_addr, 0, 0xbeefbeeb ), resp('wr', 0x01, 1,   0,  0          ), # write word  0x00000000
    req( 'wr', 0x02, base_addr, 0, 0xc0ffeebb ), resp('wr', 0x02, 1,   0,  0          ), # write word  0x00000000
    req( 'rd', 0x03, base_addr, 0, 0          ), resp('rd', 0x03, 1,   0,  0xc0ffeebb ), # read  word  0x00000000
  ]

#-------------------------------------------------------------------------
# Test cases: Write Dirty:
#-------------------------------------------------------------------------

def read_miss_dirty( base_addr=0x0 ):
  return [
    #    type  opq   addr                 len data               type  opq   test len data
    req( 'wr', 0x0, base_addr+0x00000000,  0, 0xbeefbeeb ), resp('wr', 0x0,   0,   0, 0          ), 
    req( 'rd', 0x1, base_addr+0x00010000,  0, 0          ), resp('rd', 0x1,   0,   0, 0x00c0ffee ), 
    req( 'rd', 0x2, base_addr+0x00000000,  0, 0          ), resp('rd', 0x2,   0,   0, 0xbeefbeeb ) 
  ]

def read_miss_dirty_mem( base_addr=0x0 ):
  return [
    # addr                data
    base_addr+0x00010000, 0x00c0ffee
  ]

#------------------------------------------------------------------------------
# Test case: Evict case 1
#------------------------------------------------------------------------------
# Write miss leads to evict, then immediately read hit to the cacheline

def evict_test_1( base_addr=0x0 ):
  return [
    #    type  opq   addr                 len data               type  opq   test len data
    req( 'wr', 0x0, base_addr+0x00000000,  0, 0xbeefbeeb ), resp('wr', 0x0,   0,   0, 0          ), 
    req( 'wr', 0x1, base_addr+0x00010000,  0, 0xc0ffee00 ), resp('wr', 0x1,   0,   0, 0          ), 
    req( 'rd', 0x2, base_addr+0x00010000,  0, 0          ), resp('rd', 0x2,   1,   0, 0xc0ffee00 ) 
  ]

#------------------------------------------------------------------------------
# Test case: Evict case 2
#------------------------------------------------------------------------------
# Read miss leads to evict, then immediately read hit to the cacheline

def evict_test_2( base_addr=0x0 ):
  return [
    #    type  opq   addr                 len data               type  opq   test len data
    req( 'wr', 0x0, base_addr+0x00000000,  0, 0xbeefbeeb ), resp('wr', 0x0,   0,   0, 0          ), 
    req( 'rd', 0x1, base_addr+0x00010000,  0, 0          ), resp('rd', 0x1,   0,   0, 0x00c0ffee ), 
    req( 'rd', 0x2, base_addr+0x00010000,  0, 0          ), resp('rd', 0x2,   1,   0, 0x00c0ffee ) 
  ]

def evict_mem( base_addr=0x0 ):
  return [
    # addr                data
    base_addr+0x00010000, 0x00c0ffee
  ]


#---------------------------------------------------------------------------------------------
# Test table for generic test
#---------------------------------------------------------------------------------------------

test_case_table_generic = mk_test_case_table([
  ( "                        msg_func               mem_data_func        stall lat src sink"),
  [ "read_hit_1word_clean",  read_hit_1word_clean,  None,                0.0,  1,  0,  0    ],
  [ "read_hit_many_clean",   read_hit_many_clean,   None,                0.0,  1,  0,  0    ],
  [ "read_hit_random_clean", read_hit_random_clean, None,                0.0,  1,  0,  0    ],
  [ "read_hit_1line_clean",  read_hit_1line_clean,  None,                0.0,  1,  0,  0    ],
  [ "read_hit_1word_dirty",  read_hit_1word_dirty,  None,                0.0,  1,  0,  0    ],
  [ "write_hit_clean",       write_hit_clean,       None,                0.0,  1,  0,  0    ],
  [ "write_hit_dirty",       write_hit_dirty,       None,                0.0,  1,  0,  0    ],
  [ "write_hit_1word_dirty", write_hit_1word_dirty, None,                0.0,  1,  0,  0    ],
  [ "write_hits_read_hits",  write_hits_read_hits,  None,                0.0,  1,  0,  0    ],
  [ "read_miss_1word_clean", read_miss_1word_clean, read_miss_1word_mem, 0.0,  1,  0,  0    ],
  [ "write_miss_1word_clean",write_miss_1word_clean,write_miss_1word_mem,0.0,  1,  0,  0    ],
  [ "write_miss_offset",     write_miss_offset,     None,                0.0,  1,  0,  0    ],
  [ "read_miss_dirty",       read_miss_dirty,       read_miss_dirty_mem, 0.0,  1,  0,  0    ],
  [ "evict_test_1",          evict_test_1,          None,                0.0,  1,  0,  0    ],
  [ "evict_test_2",          evict_test_2,          evict_mem,           0.0,  1,  0,  0    ],
])


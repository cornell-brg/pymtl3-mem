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
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from mem_pclib.ifcs.ReqRespMsgTypes import ReqRespMsgTypes
from BlockingCache.test.GenericTestCases import CacheGeneric_Tests

OBW  = 8   # Short name for opaque bitwidth
ABW  = 32  # Short name for addr bitwidth
DBW  = 32  # Short name for data bitwidth
CLW  = 128 # cacheline bitwidth
CacheMsg = CM = ReqRespMsgTypes(OBW, ABW, DBW)
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

class CacheDmapped_Tests:
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
  def test_dmapped_read_hit_many( s ):
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
  def test_dmapped_read_hit_random( s ):
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

  def test_dmapped_read_hit_cacheline( s ):
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
  def test_dmapped_write_hit_clean( s ):
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
  def test_dmapped_write_hit_dirty( s ):
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
  def test_dmapped_write_hits_read_hits( s ):
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
  def test_dmapped_read_miss_1word_clean( s ):
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
  def test_dmapped_write_miss_1word_clean( s ):
    msgs = [
      #    type  opq  addr       len data                type  opq test len data
      req( 'wr', 0x0, 0x00000000, 0, 0x00c0ffee ), resp( 'wr', 0x0, 0,   0, 0          ),
      req( 'rd', 0x1, 0x00000000, 0, 0          ), resp( 'rd', 0x1, 1,   0, 0x00c0ffee ),
      req( 'rd', 0x2, 0x00000008, 0, 0          ), resp( 'rd', 0x2, 1,   0, 0xeeeeeeee )
    ]
    mem = s.write_miss_1word_mem()
    s.run_test( msgs, mem, CacheMsg, MemMsg )


  def test_dmapped_write_miss_offset( s ):
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

  def test_dmapped_read_hit_1word_dirty( s ):
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

  def test_dmapped_write_hit_1word_dirty( s ):
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

  def test_dmapped_read_miss_dirty( s ):
    msgs = [
      #    type  opq   addr                 len data               type  opq   test len data
      req( 'wr', 0x0, 0x00000000,  0, 0xbeefbeeb ), resp('wr', 0x0,   0,   0, 0          ), 
      req( 'rd', 0x1, 0x00010000,  0, 0          ), resp('rd', 0x1,   0,   0, 0x00c0ffee ), 
      req( 'rd', 0x2, 0x00000000,  0, 0          ), resp('rd', 0x2,   0,   0, 0xbeefbeeb ) 
    ]
    mem = [0x00010000, 0x00c0ffee]
    s.run_test( msgs, mem, CacheMsg, MemMsg )
  
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
  def test_dmapped_read_evict_1word( s ):
    msgs = [
        #    type  opq   addr      len  data               type  opq test len  data
      req( 'wr', 0x00, 0x00002000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), # write something
      req( 'rd', 0x01, 0x000a2000, 0, 0         ), resp( 'rd', 0x01, 0, 0, 0x70facade ), # read miss on dirty line
      req( 'rd', 0x02, 0x00002000, 0, 0         ), resp( 'rd', 0x02, 0, 0, 0xffffff00 ), # read evicted address
    ]
    mem = s.evict_mem()
    s.run_test(msgs, mem, CacheMsg, MemMsg)

  #-------------------------------------------------------------------------
  # Test Case: Direct Mapped Write Evict 
  #-------------------------------------------------------------------------
  # Test cases designed for direct-mapped cache where we evict a cache line
  def test_dmapped_write_evict_1word( s ):
    msgs = [
      #    type  opq   addr      len  data               type  opq test len  data
      req( 'wr', 0x00, 0x00002000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ), #refill-write
      req( 'wr', 0x02, 0x000a2000, 0, 0x8932    ), resp( 'wr', 0x02, 0, 0, 0 ),          #evict
      req( 'rd', 0x03, 0x000a2000, 0, 0         ), resp( 'rd', 0x03, 1, 0, 0x8932 ),     #read new written data
      req( 'rd', 0x04, 0x00002000, 0, 0         ), resp( 'rd', 0x04, 0, 0, 0xffffff00 ), #read-evicted data
    ]
    mem = s.evict_mem()
    s.run_test(msgs, mem, CacheMsg, MemMsg)

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
  def test_dmapped_dir_mapped_long0_msg( s ):
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
    s.run_test(msgs, mem, CacheMsg, MemMsg)

  # #--------------------------------------------------------------------------------
  # # Generate random data and addresses
  # #--------------------------------------------------------------------------------

  # def generate_data(n):
  #   data = []
  #   for i in range(n):
  #     data.append(random.randint(0, 0xffffffff))
  #   return data

  # def generate_type(n):
  #   requestTypes = ['rd', 'wr']
  #   idx = [random.randint(0, 1) for p in range(n)]
  #   requestSequence = []
  #   for i in range(n):
  #     requestSequence.append(requestTypes[idx[i]])	
  #   return requestSequence

  # def generate_address(n):
  #   randAddr = []
  #   tagArray = []
  #   tag = (random.sample(range(4095),n))
  #   for i in range(n):
  #     #tag = random.randint(0, 4095)*256
  #     idx = random.randint(0,15)*16 + random.randint(0, 3)*4
  #     randAddr.append(tag[i]*256+idx)

  #   return randAddr

# #------------------------------------------------------------------------------
# # Test Case: Read random data from simple address patterns 
# #------------------------------------------------------------------------------

# rand_data1 = generate_data(64)
# def read_rand_data_dmap( base_addr ):
# 	read_random_data_msgs = []
# 	addr = [x*16 for x in range(16)]
# 	for i in range(16):
# 		test = 0 
# 		read_random_data_msgs.append(req('rd', i, addr[i], 0, 0))
# 		read_random_data_msgs.append(resp('rd', i, test, 0, rand_data1[i*4]))
	
# 	return read_random_data_msgs	
	
# def read_rand_data_mem( base_addr ):
# 	rand_data_mem = [];
# 	addr = [x*4 for x in range(64)]
	 
# 	for i in range(64):
# 		rand_data_mem.append(addr[i])
# 		rand_data_mem.append(rand_data1[i])
	 
# 	return rand_data_mem		

# #------------------------------------------------------------------------------
# # Test Case: Random data and request types w/ simple address patterns
# #------------------------------------------------------------------------------

# rand_data3 = generate_data(64)
# def rand_requests_dmap( base_addr ):
# 	rand_requests_msgs = []
# 	addr = [x*16 for x in range(16)]
# 	write_list = [] 
# 	for i in range(16):
# 		test = 0
# 		idx = i*4
# 		ref_memory[idx:idx+4] = rand_data3[idx:idx+4]

# 		if(rand_requests[i] == 'wr'):
# 			rand_requests_msgs.append(req('wr', i, addr[i], 0, rand_data4[i]))
# 			rand_requests_msgs.append(resp('wr', i, test, 0, 0))
# 			ref_memory[4*i] = rand_data4[i]
# 			write_list.append(i)
# 		else: #read request
# 			rand_requests_msgs.append(req('rd', i, addr[i], 0, 0))
# 			rand_requests_msgs.append(resp('rd', i, test, 0, ref_memory[4*i]))
	
# 	for i in range(len(write_list)):
# 		rand_requests_msgs.append(req('rd', 16+i, addr[write_list[i]], 0, 0))
# 		rand_requests_msgs.append(resp('rd', 16+i, 1, 0, ref_memory[4*write_list[i]]))	
			
# 	return rand_requests_msgs

# def rand_requests_mem( base_addr ):
# 	rand_data_mem = []
# 	addr = [x*4 for x in range(64)]
	 
# 	for i in range(64):
# 		rand_data_mem.append(addr[i])
# 		rand_data_mem.append(rand_data3[i])
	 
# 	return rand_data_mem			

# rand_requests = generate_type(64)
# ref_memory = [None]*64;
# rand_data4 = generate_data(64) #random data to write

# #------------------------------------------------------------------------------
# # Test Case: Unit stride with random data
# #------------------------------------------------------------------------------

# ref_memory_unit = [None]*64;
# def unit_stride_dmap( base_addr ):
# 	unit_stride_msgs = []
# 	addr = [x*4 for x in range(64)]
# 	write_list = [] 
# 	for i in range(64):
# 		if i % 4 == 0:
# 			test = 0
# 			idx = i - (i % 4);
# 			ref_memory_unit[idx:idx+4] = rand_data3[idx:idx+4]
# 		else:
# 			test = 1
		
# 		if(rand_requests[i] == 'wr'):
# 			unit_stride_msgs.append(req('wr', i, addr[i], 0, rand_data4[i]))
# 			unit_stride_msgs.append(resp('wr', i, test, 0, 0))
# 			ref_memory_unit[i] = rand_data4[i]
# 			write_list.append(i)
# 		else: #read request
# 			unit_stride_msgs.append(req('rd', i, addr[i], 0, 0))
# 			unit_stride_msgs.append(resp('rd', i, test, 0, ref_memory_unit[i]))
	
# 	for i in range(len(write_list)):
# 		unit_stride_msgs.append(req('rd', 64+i, addr[write_list[i]], 0, 0))
# 		unit_stride_msgs.append(resp('rd', 64+i, 1, 0, ref_memory_unit[write_list[i]]))	
			
# 	return unit_stride_msgs

# #------------------------------------------------------------------------------
# # Test Case: Stride with random data
# #------------------------------------------------------------------------------

# # Data to be loaded into memory before running the test
# rand_data5 = generate_data(50)
# ref_memory_stride = [None]*64;

# def stride_dmap( base_addr ):
# 	stride_msgs = []
# 	addr = [x*16**3 for x in range(50)]
# 	for i in range(50):
# 		test = 0
# 		ref_memory_stride[0] = rand_data5[i]
				
# 		if(rand_requests[i] == 'wr'):
# 			stride_msgs.append(req('wr', i, addr[i], 0, rand_data5[i]))
# 			stride_msgs.append(resp('wr', i, test, 0, 0))
# 			ref_memory_stride[0] = rand_data5[i]
# 		else: #read request
# 			stride_msgs.append(req('rd', i, addr[i], 0, 0))
# 			stride_msgs.append(resp('rd', i, test, 0, ref_memory_stride[0]))
			
# 	return stride_msgs	

# def stride_mem( base_addr ):
# 	rand_data_mem = []
# 	addr = [x*16**3 for x in range(50)]
	 
# 	for i in range(50):
# 		rand_data_mem.append(addr[i])
# 		rand_data_mem.append(rand_data5[i])
	 
# 	return rand_data_mem

# #---------------------------------------------------------------------------------------------
# # Test table for direct mapped cache tests
# #---------------------------------------------------------------------------------------------

# test_case_table_dmap = mk_test_case_table([
#   ( "                        msg_func               mem_data_func        stall lat src sink"),
#   [ "read_evict",            read_evict,            evict_mem,           0.0,  1,  0,  0    ],
#   [ "write_evict",           write_evict,           evict_mem,           0.0,  1,  0,  0    ],
#   [ "dir_mapped_long0_msg",  dir_mapped_long0_msg,  dir_mapped_long0_mem,0.0,  1,  0,  0    ],
#   [ "read_rand_data_dmap",   read_rand_data_dmap,   read_rand_data_mem,  0.0,  1,  0,  0    ],
#   [ "rand_requests_mem",     rand_requests_dmap,    rand_requests_mem,   0.0,  1,  0,  0    ],
#   [ "unit_stride_rand_data", unit_stride_dmap,      rand_requests_mem,   0.0,  1,  0,  0    ],
#   [ "stride_rand_data",      stride_dmap,           stride_mem,          0.0,  1,  0,  0    ]
# ])

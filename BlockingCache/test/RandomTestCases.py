"""
=========================================================================
RandomTestCases.py
=========================================================================
random test cases

Author : Xiaoyu Yan, Eric Tang
Date   : 16 November 2019
"""

import pytest
import struct
import random

from pymtl3 import *
from pymtl3.stdlib.test.test_utils import mk_test_case_table
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes
from BlockingCache.test.ModelCache import ModelCache

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128
CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
MemMsg = ReqRespMsgTypes(obw, abw, clw)
cacheSize = 1024

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

#--------------------------------------------------------------------------------
# Generate random data and addresses
#--------------------------------------------------------------------------------

def generate_data(n):
	data = []
	for i in range(n):
		data.append(random.randint(0, 0xffffffff))
	return data

def generate_type(n):
	requestTypes = ['rd', 'wr']
	idx = [random.randint(0, 1) for p in range(n)]
	requestSequence = []
	for i in range(n):
		requestSequence.append(requestTypes[idx[i]])	
	return requestSequence

def generate_address(n, addr_min=0, addr_max=0xffff):
	randAddr = [random.randint(addr_min,addr_max)*4 for i in range(n)]
	# tag = (random.sample(range(4095),n))
	# for i in range(n):
	# 	idx = random.randint(0,15)*16 + random.randint(0, 3)*4
	# 	randAddr.append(tag[i]*256+idx)

	return randAddr

#------------------------------------------------------------------------------
# Test Case: Read random data from simple address patterns 
#------------------------------------------------------------------------------

rand_data1 = generate_data(64)
def read_rand_data_dmap( base_addr ):
	read_random_data_msgs = []
	addr = [x*16 for x in range(16)]
	for i in range(16):
		test = 0 
		read_random_data_msgs.append(req('rd', i, addr[i], 0, 0))
		read_random_data_msgs.append(resp('rd', i, test, 0, rand_data1[i*4]))
	
	return read_random_data_msgs	
	
def read_rand_data_mem( base_addr ):
	rand_data_mem = [];
	addr = [x*4 for x in range(64)]
	 
	for i in range(64):
		rand_data_mem.append(addr[i])
		rand_data_mem.append(rand_data1[i])
	 
	return rand_data_mem		

#------------------------------------------------------------------------------
# Test Case: Random data and request types w/ simple address patterns
#------------------------------------------------------------------------------

rand_data3 = generate_data(64)
def rand_requests_dmap( base_addr ):
	rand_requests_msgs = []
	addr = [x*16 for x in range(16)]
	write_list = [] 
	for i in range(16):
		test = 0
		idx = i*4
		ref_memory[idx:idx+4] = rand_data3[idx:idx+4]

		if(rand_requests[i] == 'wr'):
			rand_requests_msgs.append(req('wr', i, addr[i], 0, rand_data4[i]))
			rand_requests_msgs.append(resp('wr', i, test, 0, 0))
			ref_memory[4*i] = rand_data4[i]
			write_list.append(i)
		else: #read request
			rand_requests_msgs.append(req('rd', i, addr[i], 0, 0))
			rand_requests_msgs.append(resp('rd', i, test, 0, ref_memory[4*i]))
	
	for i in range(len(write_list)):
		rand_requests_msgs.append(req('rd', 16+i, addr[write_list[i]], 0, 0))
		rand_requests_msgs.append(resp('rd', 16+i, 1, 0, ref_memory[4*write_list[i]]))	
			
	return rand_requests_msgs

def rand_requests_mem( base_addr ):
	rand_data_mem = []
	addr = [x*4 for x in range(64)]
	 
	for i in range(64):
		rand_data_mem.append(addr[i])
		rand_data_mem.append(rand_data3[i])
	 
	return rand_data_mem			

rand_requests = generate_type(64)
ref_memory = [None]*64;
rand_data4 = generate_data(64) #random data to write

#------------------------------------------------------------------------------
# Test Case: Unit stride with random data
#------------------------------------------------------------------------------

ref_memory_unit = [None]*64;
def unit_stride_dmap( base_addr ):
	unit_stride_msgs = []
	addr = [x*4 for x in range(64)]
	write_list = [] 
	for i in range(64):
		if i % 4 == 0:
			test = 0
			idx = i - (i % 4);
			ref_memory_unit[idx:idx+4] = rand_data3[idx:idx+4]
		else:
			test = 1
		
		if(rand_requests[i] == 'wr'):
			unit_stride_msgs.append(req('wr', i, addr[i], 0, rand_data4[i]))
			unit_stride_msgs.append(resp('wr', i, test, 0, 0))
			ref_memory_unit[i] = rand_data4[i]
			write_list.append(i)
		else: #read request
			unit_stride_msgs.append(req('rd', i, addr[i], 0, 0))
			unit_stride_msgs.append(resp('rd', i, test, 0, ref_memory_unit[i]))
	
	for i in range(len(write_list)):
		unit_stride_msgs.append(req('rd', 64+i, addr[write_list[i]], 0, 0))
		unit_stride_msgs.append(resp('rd', 64+i, 1, 0, ref_memory_unit[write_list[i]]))	
			
	return unit_stride_msgs

#------------------------------------------------------------------------------
# Test Case: Stride with random data
#------------------------------------------------------------------------------

# Data to be loaded into memory before running the test
rand_data5 = generate_data(50)
ref_memory_stride = [None]*64;

def stride_dmap( base_addr ):
	stride_msgs = []
	addr = [x*16**3 for x in range(50)]
	for i in range(50):
		test = 0
		ref_memory_stride[0] = rand_data5[i]
				
		if(rand_requests[i] == 'wr'):
			stride_msgs.append(req('wr', i, addr[i], 0, rand_data5[i]))
			stride_msgs.append(resp('wr', i, test, 0, 0))
			ref_memory_stride[0] = rand_data5[i]
		else: #read request
			stride_msgs.append(req('rd', i, addr[i], 0, 0))
			stride_msgs.append(resp('rd', i, test, 0, ref_memory_stride[0]))
			
	return stride_msgs	

def stride_mem( base_addr ):
	rand_data_mem = []
	addr = [x*16**3 for x in range(50)]
	 
	for i in range(50):
		rand_data_mem.append(addr[i])
		rand_data_mem.append(rand_data5[i])
	 
	return rand_data_mem

#------------------------------------------------------------------------------
# Test Case: Random data, requests and address
#------------------------------------------------------------------------------
# Data to be loaded into memory before running the test

rand_data6 = generate_data(50)
ref_memory_stride = [None]*64;

def stride_dmap( base_addr ):
	stride_msgs = []
	addr = [x*16**3 for x in range(50)]
	for i in range(50):
		test = 0
		ref_memory_stride[0] = rand_data5[i]
				
		if(rand_requests[i] == 'wr'):
			stride_msgs.append(req('wr', i, addr[i], 0, rand_data5[i]))
			stride_msgs.append(resp('wr', i, test, 0, 0))
			ref_memory_stride[0] = rand_data5[i]
		else: #read request
			stride_msgs.append(req('rd', i, addr[i], 0, 0))
			stride_msgs.append(resp('rd', i, test, 0, ref_memory_stride[0]))
			
	return stride_msgs	

def stride_mem( base_addr ):
	rand_data_mem = []
	addr = [x*16**3 for x in range(50)]
	 
	for i in range(50):
		rand_data_mem.append(addr[i])
		rand_data_mem.append(rand_data5[i])
	 
	return rand_data_mem

def r():
  '''
  Create random probability of stall

  returns: float between 0 and 1
  '''
  return random.random()

def l():
  '''
  Create random memory latency

  returns: int between 1 and 100
  '''
  return random.randrange(10)+1


def rand_test(n, addr_min=0, addr_max=0xffff0):
  '''
  Generates fully random sequence of transactions. Use FL model to find
  corresponding resp msgs

  :param n: length of test
  :param addr_min: min addr for address range
  :param addr_max: max addr for address range

  :returns: List of length 2n transactions
  '''
  data  = generate_data(n)
  types = generate_type(n)
  addr  = generate_address(n, addr_min, addr_max)
  msgs = [0] * ( 2*n)
  for i in range(n):
    if types[i] == 'wr':
      msgs[2*i] = req(types[i], i, addr[i], 0, data[i])
    else:
      msgs[2*i] = req(types[i], i, addr[i], 0, 0)

  # print (msgs)
  return msgs

def rand_mem(addr_min=0, addr_max=0xfff):
  '''
  Randomly generate start state for memory

  :returns: list of memory addresses w/ random data values
  '''
  mem = []

  curr_addr = addr_min
  while curr_addr <= addr_max:
    d = generate_data(1)
    mem.append(curr_addr)
    mem.append(d[0])
    curr_addr += 4 
  return mem

def gen_fully_random_table(max_size=1000):
  '''
  Create table of fully random cache requests and mem
  
  :returns: fully random test case table
  '''

  table = [( "                        msg_func               mem_data_func        stall lat src sink")]
  for i in range(max_size):
    test_name = 'rand test ' + str(i)
    n = random.randint(1,1000)
    tests = rand_test(n)
    mem = rand_mem()
    table.append([test_name, tests, mem, r(), l(), l(), l()])

  return table

#-------------------------------------------------------------------------
# Test: Randomly read or write random data from random low addresses
#-------------------------------------------------------------------------
def rand_rw_alladdr( mem=None ):
  
  model = ModelCache(cacheSize, 1, 1, clw, mem)

  RAND_LEN = random.randint(1,20)

  data  = generate_data(RAND_LEN)
  types = generate_type(RAND_LEN)
  addr  = generate_address(RAND_LEN)
  for i in range(RAND_LEN):
    if types[i] == 'wr':
      # Write something
      model.write(addr[i] & Bits32(0xfffffffc), data[i])
    else:
      # Read something
      model.read(addr[i] & Bits32(0xfffffffc))

  return model.get_transactions()

#-------------------------------------------------------------------------
# Test: Randomly read or write random data from random low addresses
#-------------------------------------------------------------------------
def rand_small_addr_range( mem=None ):
  
  model = ModelCache(cacheSize, 1, 0, clw, mem)

  RAND_LEN = random.randint(1,20)

  data  = generate_data(RAND_LEN)
  types = generate_type(RAND_LEN)
  addr  = generate_address(RAND_LEN,0x10,0x100)
  for i in range(RAND_LEN):
    if types[i] == 'wr':
      # Write something
      model.write(addr[i] & Bits32(0xfffffffc), data[i])
    else:
      # Read something
      model.read(addr[i] & Bits32(0xfffffffc))

  return model.get_transactions()



#---------------------------------------------------------------------------------------------
# Test table for random direct mapped cache tests
#---------------------------------------------------------------------------------------------

test_case_table_random = mk_test_case_table([
  ( "                        msg_func               mem_data_func        stall lat src sink"),
  [ "read_rand_data_dmap",   read_rand_data_dmap,   read_rand_data_mem,  0.0,  1,   0,   0  ],
  [ "rand_requests",         rand_requests_dmap,    rand_requests_mem,   0.0,  1,   0,   0  ],
  [ "unit_stride_rand_data", unit_stride_dmap,      rand_requests_mem,   0.0,  1,   0,   0  ],
  [ "stride_rand_data",      stride_dmap,           stride_mem,          0.0,  1,   0,   0  ]
])

test_case_table_random_lat = mk_test_case_table([
  ( "                        msg_func               mem_data_func        stall lat src sink"),
  [ "read_rand_data_dmap",   read_rand_data_dmap,   read_rand_data_mem,  0.0,  1,   0,   0  ],
  [ "read_rand_data_stall",  read_rand_data_dmap,   read_rand_data_mem,  r(),  1,   0,   0  ],
  [ "read_rand_data_lat",    read_rand_data_dmap,   read_rand_data_mem,  0.0,  l(), 0,   0  ],
  [ "read_rand_stall_lat",   read_rand_data_dmap,   read_rand_data_mem,  r(),  l(), 0,   0  ],
  [ "rand_src_sink_delay",   read_rand_data_dmap,   read_rand_data_mem,  r(),  l(), l(), l()],
  [ "rand_requests",         rand_requests_dmap,    rand_requests_mem,   0.0,  1,   0,   0  ],
  [ "unit_stride_rand_data", unit_stride_dmap,      rand_requests_mem,   0.0,  1,   0,   0  ],
  [ "stride_rand_data",      stride_dmap,           stride_mem,          0.0,  1,   0,   0  ],
])

test_case_table_enhanced_random = mk_test_case_table([
  ( "                        msg_func               mem_data_func        stall lat src sink"),
  [ "completely_random",     rand_rw_alladdr,       rand_mem,            0.0,  1,   0,  0   ],
  [ "completely_random",     rand_rw_alladdr,       rand_mem,            r(),  l(), l(), l()],
  [ "rand_small_addr_range",     rand_small_addr_range, rand_mem,            0.0,  1,   0,  0],
])


"""
=========================================================================
 DmappedTestCases.py
=========================================================================
Direct mapped test cases

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


#-------------------------------------------------------------------------
# Test Case: test direct-mapped
#-------------------------------------------------------------------------
# Test cases designed for direct-mapped cache. We should set check_test
# to False if we use it to test set-associative cache.

def dir_mapped_long0_msg( base_addr ):
  return [
    #    type  opq   addr      len  data               type  opq test len  data
    # Write to cacheline 0
    req( 'wr', 0x00, 0x00000000, 0, 0xffffff00), resp( 'wr', 0x00, 0, 0, 0          ),
    req( 'wr', 0x01, 0x00000004, 0, 0xffffff01), resp( 'wr', 0x01, 1, 0, 0          ),
    req( 'wr', 0x02, 0x00000008, 0, 0xffffff02), resp( 'wr', 0x02, 1, 0, 0          ),
    req( 'wr', 0x03, 0x0000000c, 0, 0xffffff03), resp( 'wr', 0x03, 1, 0, 0          ),
    # Write to cacheline 0
    req( 'wr', 0x04, 0x00001000, 0, 0xffffff04), resp( 'wr', 0x04, 0, 0, 0          ),
    req( 'wr', 0x05, 0x00001004, 0, 0xffffff05), resp( 'wr', 0x05, 1, 0, 0          ),
    req( 'wr', 0x06, 0x00001008, 0, 0xffffff06), resp( 'wr', 0x06, 1, 0, 0          ),
    req( 'wr', 0x07, 0x0000100c, 0, 0xffffff07), resp( 'wr', 0x07, 1, 0, 0          ),
    # Evict cache 0
    req( 'rd', 0x08, 0x00002000, 0, 0         ), resp( 'rd', 0x08, 0, 0, 0x00facade ),
    # Read again from same cacheline
    req( 'rd', 0x09, 0x00002004, 0, 0         ), resp( 'rd', 0x09, 1, 0, 0x05ca1ded ),
    # Read from cacheline 0
    req( 'rd', 0x0a, 0x00001004, 0, 0         ), resp( 'rd', 0x0a, 0, 0, 0xffffff05 ),
    # Write to cacheline 0
    req( 'wr', 0x0b, 0x0000100c, 0, 0xffffff09), resp( 'wr', 0x0b, 1, 0, 0          ),
    # Read that back
    req( 'rd', 0x0c, 0x0000100c, 0, 0         ), resp( 'rd', 0x0c, 1, 0, 0xffffff09 ),
    # Evict cache 0 again
    req( 'rd', 0x0d, 0x00000000, 0, 0         ), resp( 'rd', 0x0d, 0, 0, 0xffffff00 ),
    # Testing cacheline 7 now
    # Write to cacheline 7
    req( 'wr', 0x10, 0x00000070, 0, 0xffffff00), resp( 'wr', 0x10, 0, 0, 0          ),
    req( 'wr', 0x11, 0x00000074, 0, 0xffffff01), resp( 'wr', 0x11, 1, 0, 0          ),
    req( 'wr', 0x12, 0x00000078, 0, 0xffffff02), resp( 'wr', 0x12, 1, 0, 0          ),
    req( 'wr', 0x13, 0x0000007c, 0, 0xffffff03), resp( 'wr', 0x13, 1, 0, 0          ),
    # Write to cacheline 7
    req( 'wr', 0x14, 0x00001070, 0, 0xffffff04), resp( 'wr', 0x14, 0, 0, 0          ),
    req( 'wr', 0x15, 0x00001074, 0, 0xffffff05), resp( 'wr', 0x15, 1, 0, 0          ),
    req( 'wr', 0x16, 0x00001078, 0, 0xffffff06), resp( 'wr', 0x16, 1, 0, 0          ),
    req( 'wr', 0x17, 0x0000107c, 0, 0xffffff07), resp( 'wr', 0x17, 1, 0, 0          ),
    # Evict cacheline 7
    req( 'rd', 0x18, 0x00002070, 0, 0         ), resp( 'rd', 0x18, 0, 0, 0x70facade ),
    # Read again from same cacheline
    req( 'rd', 0x19, 0x00002074, 0, 0         ), resp( 'rd', 0x19, 1, 0, 0x75ca1ded ),
    # Read from cacheline 7
    req( 'rd', 0x1a, 0x00001074, 0, 0         ), resp( 'rd', 0x1a, 0, 0, 0xffffff05 ),
    # Write to cacheline 7 way 1 to see if cache hits properly
    req( 'wr', 0x1b, 0x0000107c, 0, 0xffffff09), resp( 'wr', 0x1b, 1, 0, 0          ),
    # Read that back
    req( 'rd', 0x1c, 0x0000107c, 0, 0         ), resp( 'rd', 0x1c, 1, 0, 0xffffff09 ),
    # Evict cacheline 0 again
    req( 'rd', 0x1d, 0x00000070, 0, 0         ), resp( 'rd', 0x1d, 0, 0, 0xffffff00 ),
  ]

def dir_mapped_long0_mem( base_addr ):
  return [
    # addr      # data (in int)
    0x00002000, 0x00facade,
    0x00002004, 0x05ca1ded,
    0x00002070, 0x70facade,
    0x00002074, 0x75ca1ded,
  ]

#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Generate random data and addresses
#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
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

def generate_address(n):
	randAddr = []
	tagArray = []
	tag = (random.sample(range(4095),n))
	for i in range(n):
		#tag = random.randint(0, 4095)*256
		idx = random.randint(0,15)*16 + random.randint(0, 3)*4
		randAddr.append(tag[i]*256+idx)

	return randAddr

#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# RANDOM TEST: Simple address patterns, read request, random data --dmap
#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
rand_data1 = generate_data(64)

def read_rand_data_dmap( base_addr ):
	read_random_data_msgs = []
	addr = [x*16 for x in range(16)]
	for i in range(16):
		test = 0 
		read_random_data_msgs.append(req('rd', i, addr[i], 0, 0))
		read_random_data_msgs.append(resp('rd', i, test, 0, rand_data1[i*4]))
	
	return read_random_data_msgs	
	
# Data to be loaded into memory before running the test

def read_rand_data_mem( base_addr ):
	rand_data_mem = [];
	addr = [x*4 for x in range(64)]
	 
	for i in range(64):
		rand_data_mem.append(addr[i])
		rand_data_mem.append(rand_data1[i])
	 
	return rand_data_mem		

#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Simple address patterns, random request types and data --dmap
#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

# Data to be loaded into memory before running the test
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

#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Unit stride with random data --dmap
#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
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

#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# Stride with random data --dmap
#'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

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

#---------------------------------------------------------------------------------------------
# Test table for dmapped test
#---------------------------------------------------------------------------------------------

test_case_table_dmap = mk_test_case_table([
  ( "                        msg_func               mem_data_func        stall lat src sink"),
  [ "dir_mapped_long0_msg",  dir_mapped_long0_msg,  dir_mapped_long0_mem,0.0,  1,  0,  0    ],
  [ "read_rand_data_dmap",   read_rand_data_dmap,   read_rand_data_mem,  0.0,  1,  0,  0    ],
  [ "rand_requests_mem",     rand_requests_dmap,    rand_requests_mem,   0.0,  1,  0,  0    ],
  [ "unit_stride_dmap",      unit_stride_dmap,      rand_requests_mem,   0.0,  1,  0,  0    ],
  [ "stride_dmap",           stride_dmap,           stride_mem,          0.0,  1,  0,  0    ],

])
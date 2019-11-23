"""
=========================================================================
BlockingCacheRTL_test.py
=========================================================================
Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 22 November 2019
"""

import pytest
import random
from pymtl3      import *
from BlockingCache.test.BlockingCacheFL_test import test_case_table_generic, \
  TestHarness, run_sim, setup_tb
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.test.GenericTestCases import test_case_table_generic
from BlockingCache.test.GenericTestCases import CacheMsg as GenericCacheMsg
from BlockingCache.test.GenericTestCases import MemMsg   as GenericMemMsg
from BlockingCache.test.GenericTestCases import cacheSize  as GenericcacheSize
from BlockingCache.test.DmappedTestCases import test_case_table_dmap
from BlockingCache.test.DmappedTestCases import CacheMsg as DmapCacheMsg
from BlockingCache.test.DmappedTestCases import MemMsg   as DmapMemMsg
from BlockingCache.test.DmappedTestCases import cacheSize  as DmapcacheSize
from BlockingCache.test.RandomTestCases  import test_case_table_random, test_case_table_random_lat,\
  test_case_table_enhanced_random, complete_random_test, rand_mem
from BlockingCache.test.RandomTestCases import CacheMsg  as RandomCacheMsg
from BlockingCache.test.RandomTestCases import MemMsg    as RandomMemMsg
from BlockingCache.test.RandomTestCases import cacheSize as RandomcacheSize
from pymtl3.passes.yosys import TranslationImportPass


from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes

base_addr = 0x74
max_cycles = 10000

#-------------------------------------------------------------------------
# Translate Function for the cache
#-------------------------------------------------------------------------

def translate(model):
  # Translate the checksum unit and import it back in using the yosys
  # backend
  model.cache.yosys_translate_import = True
  model = TranslationImportPass(  )( model )

#-------------------------------------------------------------------------
# Generic tests for both baseline and alternative design
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_generic )
def test_generic( test_params, test_verilog ):
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func(base_addr)
  else: 
    mem = None
  setup_tb( test_params.msg_func( base_addr ), 
  mem, BlockingCachePRTL, 
  GenericcacheSize, GenericCacheMsg, GenericMemMsg, 
  test_params.stall, test_params.lat, test_params.src, 
  test_params.sink, 1 )


#-------------------------------------------------------------------------
# Direct Mapped tests
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_dmap )
def test_dmap( test_params, test_verilog ):
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func(base_addr)
  else: 
    mem = None
  setup_tb( test_params.msg_func( base_addr ), 
  mem, BlockingCachePRTL, 
  DmapcacheSize, DmapCacheMsg, DmapMemMsg, 
  test_params.stall, test_params.lat, test_params.src, 
  test_params.sink, 1 )

#-------------------------------------------------------------------------
# Random Tests
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_random )
def test_random( test_params, test_verilog ):
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func(base_addr)
  else: 
    mem = None
  setup_tb( test_params.msg_func( base_addr ), 
  mem, BlockingCachePRTL, 
  RandomcacheSize, RandomCacheMsg, RandomMemMsg, 
  test_params.stall, test_params.lat, test_params.src, 
  test_params.sink, 1 )

@pytest.mark.parametrize( **test_case_table_random_lat )
def test_random( test_params, test_verilog ):
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func(base_addr)
  else: 
    mem = None
  setup_tb( test_params.msg_func( base_addr ), 
  mem, BlockingCachePRTL, 
  RandomcacheSize, RandomCacheMsg, RandomMemMsg, 
  test_params.stall, test_params.lat, test_params.src, 
  test_params.sink, 1 )


@pytest.mark.parametrize( **test_case_table_enhanced_random )
def test_rand_trans( test_params, test_verilog ):
  mem = test_params.mem_data_func(base_addr)
  setup_tb( test_params.msg_func( mem ), 
  mem, BlockingCachePRTL, 
  RandomcacheSize, RandomCacheMsg, RandomMemMsg, 
  test_params.stall, test_params.lat, test_params.src, 
  test_params.sink, 1 )

def test_rand_param_trans(test_verilog):
  obw  = 8   # Short name for opaque bitwidth
  abw  = 32  # Short name for addr bitwidth
  dbw  = 32  # Short name for data bitwidth
  addr_min = 0
  addr_max = 200
  num_trans = 50
  
  # clw = 512 # minimum cacheline size is 64 bits
  # cacheSize = 1024 #minimu, cacheSize is 2 times clw
  clw  = 2**(6+random.randint(0,4)) # minimum cacheline size is 64 bits
  cacheSize = 2**( clog2(clw) + random.randint(1,6)) #minimum cacheSize is 2 times clw
  idw = clog2(cacheSize//clw)         # index width; clog2(512) = 9
  ofw = clog2(clw//8)      # offset bitwidth; clog2(128/8) = 4
  tgw = abw - ofw - idw    # tag bitwidth; 32 - 4 - 9 = 19
  CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
  MemMsg = ReqRespMsgTypes(obw, abw, clw)
  mem = rand_mem(addr_min, addr_max)
  msg =  complete_random_test(mem, addr_min, addr_max, num_trans, cacheSize, clw)
  print( f"clw={clw} size={cacheSize} idw={idw} ofw={ofw} tgw={tgw}")
  setup_tb( msg, 
  mem, BlockingCachePRTL, 
  cacheSize, CacheMsg, MemMsg, 
  0, 1, 0, 0, 1 )

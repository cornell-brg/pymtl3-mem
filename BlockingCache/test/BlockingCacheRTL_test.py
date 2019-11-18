"""
=========================================================================
BlockingCacheRTL_test.py
=========================================================================
Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 15 November 2019
"""

import pytest
from pymtl3      import *
from BlockingCache.test.BlockingCacheFL_test import test_case_table_generic, \
  TestHarness, run_sim
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.test.GenericTestCases import test_case_table_generic
from BlockingCache.test.GenericTestCases import CacheMsg as GenericCacheMsg
from BlockingCache.test.GenericTestCases import MemMsg   as GenericMemMsg
from BlockingCache.test.DmappedTestCases import test_case_table_dmap
from BlockingCache.test.DmappedTestCases import CacheMsg as DmapCacheMsg
from BlockingCache.test.DmappedTestCases import MemMsg   as DmapMemMsg
<<<<<<< HEAD
from BlockingCache.test.RandomTestCases  import test_case_table_random
from BlockingCache.test.RandomTestCases import CacheMsg as RandomCacheMsg
from BlockingCache.test.RandomTestCases import MemMsg   as RandomMemMsg
=======
from pymtl3.passes.yosys import TranslationImportPass
>>>>>>> 87ee2ac3ac07464a9a63ad71ae417b7c616cc0bf

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
def test_generic( test_params ):
  msgs = test_params.msg_func( base_addr )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( base_addr )
  # Instantiate testharness
  harness = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         BlockingCachePRTL, GenericCacheMsg,
                         GenericMemMsg)
  harness.elaborate()
  translate(harness)
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, max_cycles )

@pytest.mark.parametrize( **test_case_table_dmap )
def test_dmap( test_params ):
  msgs = test_params.msg_func( base_addr )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( base_addr )
  # Instantiate testharness
  harness = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         BlockingCachePRTL, DmapCacheMsg,
                         DmapMemMsg)
  harness.elaborate()
  # translate()
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, max_cycles )

@pytest.mark.parametrize( **test_case_table_random )
def test_random( test_params ):
  msgs = test_params.msg_func( base_addr )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( base_addr )
  # Instantiate testharness
  harness = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         BlockingCachePRTL, RandomCacheMsg,
                         RandomMemMsg)
  harness.elaborate()
  # translate()
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, max_cycles )


#-------------------------------------------------------------------------
# Tests only for two-way set-associative cache
#-------------------------------------------------------------------------

# @pytest.mark.parametrize( **test_case_table_set_assoc )
# def test_set_assoc( test_params, dump_vcd, test_verilog ):
#   return 0
  # msgs = test_params.msg_func( 0 )
  # if test_params.mem_data_func != None:
  #   mem  = test_params.mem_data_func( 0 )
  # # Instantiate testharness
  # harness = TestHarness( msgs[::2], msgs[1::2],
  #                        test_params.stall, test_params.lat,
  #                        test_params.src, test_params.sink,
  #                        NonblockingCacheRTL, True, dump_vcd, test_verilog )
  # # Load memory before the test
  # if test_params.mem_data_func != None:
  #   harness.load( mem[::2], mem[1::2] )
  # # Run the test
  # run_sim( harness, dump_vcd )


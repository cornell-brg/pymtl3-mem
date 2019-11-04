"""
#=========================================================================
# BlockingCacheRTL_test.py
#=========================================================================
Test for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 11/04/19
"""

import pytest
from pymtl3      import *
from BlockingCache.test.BlockingCacheFL_test import test_case_table_generic, \
  TestHarness, run_sim
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.test.GenericTestCases import test_case_table_generic
from BlockingCache.test.GenericTestCases import CacheMsg as GenericCacheMsg
from BlockingCache.test.GenericTestCases import MemMsg   as GenericMemMsg

base_addr = 0x74
max_cycles = 50

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
  # translate()
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, max_cycles )

# @pytest.mark.parametrize( **test_case_table_dir_mapped )
# def test_dir_mapped( test_params, dump_vcd, test_verilog ):
#   msgs = test_params.msg_func( 0 )
#   if test_params.mem_data_func != None:
#     mem  = test_params.mem_data_func( 0 )
#   # Instantiate testharness
#   harness = TestHarness( msgs[::2], msgs[1::2],
#                          test_params.stall, test_params.lat,
#                          test_params.src, test_params.sink,
#                          NonblockingCacheRTL, True, dump_vcd, test_verilog )
#   # Load memory before the test
#   if test_params.mem_data_func != None:
#     harness.load( mem[::2], mem[1::2] )
#   # Run the test
#   run_sim( harness, dump_vcd )



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


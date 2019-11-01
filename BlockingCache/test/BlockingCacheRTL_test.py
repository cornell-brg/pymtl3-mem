#=========================================================================
# BlockingCacheRTL_test.py
#=========================================================================
import pytest
from pymtl3      import *
from BlockingCache.test.BlockingCacheFL_test import test_case_table_generic, TestHarness, run_sim
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL

#-------------------------------------------------------------------------
# Generic tests for both baseline and alternative design
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_generic )
def test_generic( test_params ):
  msgs = test_params.msg_func( 100 )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( 0 )
  # Instantiate testharness
  harness = TestHarness( msgs[::2], msgs[1::2],
                         test_params.stall, test_params.lat,
                         test_params.src, test_params.sink,
                         BlockingCachePRTL)
  harness.elaborate()
  # translate()
  # Load memory before the test
  if test_params.mem_data_func != None:
    harness.load( mem[::2], mem[1::2] )
  # Run the test
  run_sim( harness, max_cycles=20 )

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


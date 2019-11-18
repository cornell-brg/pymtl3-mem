"""
=========================================================================
BlockingCacheRTL_test.py
=========================================================================
Tests for Pipelined Blocking Cache RTL model 

Author : Xiaoyu Yan, Eric Tang
Date   : 17 November 2019
"""

import pytest
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
from BlockingCache.test.Asso2WayTestCases import test_case_table_asso_2way
from BlockingCache.test.Asso2WayTestCases import CacheMsg  as Asso2CacheMsg
from BlockingCache.test.Asso2WayTestCases import MemMsg    as Asso2MemMsg
from BlockingCache.test.Asso2WayTestCases import cacheSize as Asso2cacheSize
from pymtl3.passes.yosys import TranslationImportPass

base_addr = 0x74
max_cycles = 500

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
  stall = test_params.stall
  lat   = test_params.lat
  src   = test_params.src
  sink  = test_params.sink
  
  msg = test_params.msg_func( base_addr )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( base_addr )
  else:
    mem = None
  setup_tb( msg, mem, BlockingCachePRTL, GenericcacheSize, 
  GenericCacheMsg, GenericMemMsg, 
  stall, lat, src, sink, 1 )

@pytest.mark.parametrize( **test_case_table_dmap )
def test_dmap( test_params ):
  stall = test_params.stall
  lat   = test_params.lat
  src   = test_params.src
  sink  = test_params.sink
  msg = test_params.msg_func( base_addr )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( base_addr )
  else:
    mem = None
  setup_tb( msg, mem, BlockingCachePRTL, DmapcacheSize, 
  GenericCacheMsg, GenericMemMsg, 
  stall, lat, src, sink, 1 )

#-------------------------------------------------------------------------
# Tests only for two-way set-associative cache
#-------------------------------------------------------------------------

@pytest.mark.parametrize( **test_case_table_asso_2way )
def test_asso2( test_params, dump_vcd, test_verilog ):
  stall = test_params.stall
  lat   = test_params.lat
  src   = test_params.src
  sink  = test_params.sink
  msg = test_params.msg_func( base_addr )
  if test_params.mem_data_func != None:
    mem = test_params.mem_data_func( base_addr )
  else:
    mem = None
  setup_tb( msg, mem, BlockingCachePRTL, Asso2cacheSize, 
  GenericCacheMsg, GenericMemMsg, 
  stall, lat, src, sink, 2 )



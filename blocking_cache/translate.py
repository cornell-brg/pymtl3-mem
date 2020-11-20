#!/usr/bin/env python
#=========================================================================
# translate.py
#=========================================================================
# Translates the Blocking Cache to System Verilog
#
# Author : Xiaoyu Yan, Eric Tang
# Date   : 23 December 2019

import argparse
import os
import sys
import fileinput
import subprocess

file_path   = os.path.abspath( __file__ )
dir_path    = os.path.dirname( file_path )
parent_path = os.path.dirname( dir_path )
sys.path.insert( 0, parent_path )
sram_wrapper_file = os.path.join( parent_path, 'sram', 'brg_gf14_sram_generic_synopsys.v' )

# Import the translation pass from verilog backend
from pymtl3.passes.backends.verilog import (
        VerilogTranslationPass,
        VerilogTranslationImportPass,
        VerilogPlaceholderPass,
)

# Import the Cache generator
from blocking_cache.BlockingCacheRTL import BlockingCacheRTL
from mem_ifcs.MemMsg import MemMsgType, mk_mem_msg

#=========================================================================
# Command line processing
#=========================================================================

def parse_cmdline():
  p = argparse.ArgumentParser(description='Translate the cache with some params')
  # Additional commane line arguments for the translator
  p.add_argument( "--output-dir", default="", type=str )
  p.add_argument( "--size", default=4096, type=int )
  p.add_argument( "--clw", default=128, type=int )
  p.add_argument( "--dbw", default=32, type=int )
  p.add_argument( "--abw", default=32, type=int )
  p.add_argument( "--obw", default=8, type=int )
  p.add_argument( "--asso", default=2, type=int )
  p.add_argument( '--replace-sram', action='store_true', help="Replace SRAM model with real SRAM wrapper" )
  opts = p.parse_args()
  return opts

#=========================================================================
# Replace SRAM
#=========================================================================

def replace_sram( file_name ):

  with fileinput.input( file_name, inplace=True ) as f:
    for line in f:
      if "SramGenericPRTL__num_bits_128__num_words_256 sram" in line.rstrip('\r\n'):
        new_line = line.replace( "SramGenericPRTL__num_bits_128__num_words_256 sram",
                                 "SramGenericPRTL #(.num_bits(128) , .num_words(256)) sram" )
        print( new_line, end='' )
      elif "SramGenericPRTL__num_bits_26__num_words_128 sram" in line.rstrip('\r\n'):
        new_line = line.replace( "SramGenericPRTL__num_bits_26__num_words_128 sram",
                                 "SramGenericPRTL #(.num_bits(26) , .num_words(128)) sram" )
        print( new_line, end='' )
      else:
        print( line, end='' )

#=========================================================================
# Runs the translation script
#=========================================================================

def main( opts ):
  CacheReqType, CacheRespType = mk_mem_msg(opts.obw, opts.abw, opts.dbw, has_wr_mask=False)
  MemReqType, MemRespType = mk_mem_msg(opts.obw, opts.abw, opts.clw)
  # Instantiate the cache
  dut = BlockingCacheRTL( CacheReqType, CacheRespType, MemReqType,
                          MemRespType, opts.size, opts.asso )
  success = False
  module_name = f"BlockingCache_{opts.size}_{opts.clw}_{opts.abw}_{opts.dbw}_{opts.asso}"
  file_name = module_name + ".v"

  dut.set_metadata( VerilogTranslationPass.enable, True )
  dut.set_metadata( VerilogTranslationPass.explicit_file_name, module_name )
  dut.set_metadata( VerilogTranslationPass.explicit_module_name, module_name )

  # dut.verilog_translate = True
  # dut.config_verilog_translate = TranslationConfigs(
  #     explicit_module_name = module_name,
  #     explicit_file_name = file_name
  #   )

  try:
    dut.elaborate()
    dut.apply( VerilogTranslationPass() )
    success = True
  finally:
    if success:
      # path = os.path.join(os.getcwd(), f"{dut.translated_top_module_name}.sv")
      print("\nTranslation finished successfully!")
      # print(f"You can find the generated SystemVerilog file at {path}.")
      return file_name
    else:
      print("\nTranslation failed!")
      return None

if __name__ == "__main__":
  opts = parse_cmdline()
  file_name = main( opts )

  if opts.replace_sram:
    assert os.path.isfile( sram_wrapper_file ), f"SRAM Wrapper file ({sram_wrapper_file}) doesn't exist"
    replace_sram( file_name )

    # concat wrapper
    bashCommand = f"cat {sram_wrapper_file} >> {file_name}"
    # print( bashCommand )
    process = subprocess.Popen(bashCommand, stdout=subprocess.PIPE, shell=True)
    output, error = process.communicate()

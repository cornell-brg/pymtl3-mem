"""
=========================================================================
translate.py
=========================================================================
Translates the Blocking Cache to System Verilog

Author : Xiaoyu Yan, Eric Tang
Date   : 23 December 2019
"""

import argparse
import os
import sys

sys.path.append('../')

# Import the translation pass from verilog backend
from pymtl3.passes.backends.verilog import TranslationConfigs, TranslationPass

# Import the Cache generator
from blocking_cache.BlockingCacheRTL import BlockingCacheRTL
from pymtl3.stdlib.ifcs.MemMsg import MemMsgType, mk_mem_msg

obw       = 8   # Short name for opaque bitwidth
abw       = 32  # Short name for addr bitwidth
dbw       = 32  # Short name for data bitwidth
clw       = 128
cacheSize = 4096
CacheReqType, CacheRespType = mk_mem_msg(obw, abw, dbw)
MemReqType, MemRespType = mk_mem_msg(obw, abw, clw)

#=========================================================================
# Command line processing
#=========================================================================

def parse_cmdline():

  # Standard command line arguments
  p.add_argument( "-h", "--help", action="store_true" )

  # Additional commane line arguments for the translator
  p.add_argument( "--output-dir", default="", type=valid_dir )

  opts = p.parse_args()
  if opts.help: p.error()
  return opts


def main():
  opts = parse_cmdline()
  # If output directory was specified, change to that directory
  # if opts.output_dir:
  #   os.chdir( opts.output_dir )

  # Instantiate the cache
  dut = BlockingCacheRTL(CacheReqType, CacheRespType, MemReqType, \
    MemRespType, cacheSize)

  # Tag the processor as to be translated
  dut.verilog_translate = True
  # Perform translation
  success = False
  dut.config_verilog_translate = TranslationConfigs() 

  try:
    dut.elaborate()
    dut.apply( TranslationPass() )
    success = True
  finally:
    if success:
      # path = os.path.join(os.getcwd(), f"{dut.translated_top_module_name}.sv")
      print("\nTranslation finished successfully!")
      # print(f"You can find the generated SystemVerilog file at {path}.")
    else:
      print("\nTranslation failed!")


if __name__ == "__main__":
  main()

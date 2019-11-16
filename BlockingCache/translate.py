"""
=========================================================================
translate.py
=========================================================================
Translates the Blocking Cache to System Verilog

Author : Xiaoyu Yan, Eric Tang
Date   : 15 November 2019
"""

import argparse
import os
import sys

import pytest
from pymtl3      import *
from pymtl3.passes.yosys import TranslationImportPass, TranslationPass # Translation to Verilog
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from BlockingCache.ReqRespMsgTypes import ReqRespMsgTypes

obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128
cacheSize = 4098
CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
MemMsg = ReqRespMsgTypes(obw, abw, clw)


def test_main():
  dut = BlockingCachePRTL(cacheSize, CacheMsg, MemMsg)
  dut.yosys_translate = True
  success = False
  try:
    dut.elaborate()
    dut.apply( TranslationPass() )
    success = True
  finally:
    if success:
    #   path = os.getcwd() + \
    #          "/{}.sv".format(dut.translated_top_module_name)

      # if opts.output_dir:
      #   # Upon success, symlink the file to outputs/design.v which is the
      #   # handoff point to alloy-asic
      #   design_v = os.getcwd() + "/outputs/design.v"

      #   # If design.v exists then delete it
      #   if os.path.exists( design_v ):
      #     os.remove( design_v )

      #   os.symlink( path, design_v )

      print("\nTranslation finished successfully!")
      # print(f"You can find the generated SystemVerilog file at {path}.")
    else:
      print()
      print("\nTranslation failed!")


if __name__ == "__main__":
  main()
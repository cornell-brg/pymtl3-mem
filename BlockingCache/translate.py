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

# Import the translation pass from yosys backend
from pymtl3.passes.backends.yosys import TranslationPass

# Import the Cache generator
from BlockingCache.BlockingCachePRTL import BlockingCachePRTL
from mem_pclib.ifcs.ReqRespMsgTypes import ReqRespMsgTypes


obw  = 8   # Short name for opaque bitwidth
abw  = 32  # Short name for addr bitwidth
dbw  = 32  # Short name for data bitwidth
clw  = 128
cacheSize = 4098
CacheMsg = ReqRespMsgTypes(obw, abw, dbw)
MemMsg = ReqRespMsgTypes(obw, abw, clw)

#=========================================================================
# Command line processing
#=========================================================================

class ArgumentParserWithCustomError(argparse.ArgumentParser):
  def error( self, msg = "" ):
    if ( msg ): print("\n"+f" ERROR: {msg}")
    print("")
    file = open( sys.argv[0] )
    for ( lineno, line ) in enumerate( file ):
      if ( line[0] != '#' ): sys.exit(msg != "")
      if ( (lineno == 2) or (lineno >= 4) ): print(line[1:].rstrip("\n"))


def parse_cmdline():
  def valid_dir(string):
    assert not string or (os.path.isdir(string) and os.path.exists(string)), \
      "the given path {} does not exist or is not a directory!".format(string)
    return string

  p = ArgumentParserWithCustomError( add_help=False )

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
  if opts.output_dir:
    os.chdir( opts.output_dir )

  # Instantiate the cache
  dut = BlockingCachePRTL(cacheSize, CacheMsg, MemMsg)

  # Tag the processor as to be translated
  dut.yosys_translate = True

  # Perform translation
  success = False

  try:
    dut.elaborate()
    dut.apply( TranslationPass() )
    success = True
  finally:
    if success:
      path = os.path.join(os.getcwd(), f"{dut.translated_top_module_name}.sv")
      print("\nTranslation finished successfully!")
      print(f"You can find the generated SystemVerilog file at {path}.")
    else:
      print("\nTranslation failed!")


if __name__ == "__main__":
  main()

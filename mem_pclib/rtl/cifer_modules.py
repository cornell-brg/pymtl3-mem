"""
=========================================================================
 cifer_modules.py
=========================================================================
Our own version of registers that handles bitstructs better

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

class DirtyMaskGen( Components ):
  """
  Generates the dirty bit per word mask at the M0 stage to be written into 
  the Tag array SRAM
  """
  def construct( s, p ):


class DirtyBitsDecoder( Components ):
  """
  Arbitrates the dirty cache line.
  If we have a hit, then we check for dirty bits at the word level.
  If we have a miss, then we check for dirty bits at the line level.
  This block will output is_dirty based on these facts. 
  """

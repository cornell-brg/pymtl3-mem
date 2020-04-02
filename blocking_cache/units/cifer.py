"""
=========================================================================
cifer.py
=========================================================================
Modules used in cifer project

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   17 March 2020
"""

from pymtl3 import *

class DirtyLineDetector( Component ):
  """
  Arbitrates the dirty cache line.
  If we have a hit, then we check for dirty bits at the word level.
  If we have a miss, then we check for dirty bits at the line level.
  This block will output is_dirty based on these facts.
  """

  def construct( s, p ):
    s.wd_en      = InPort ( Bits1 )
    s.offset     = InPort ( p.BitsOffset )
    s.dirty_bits = InPort ( p.BitsDirty )
    s.is_dirty   = OutPort( Bits1 )

    bitwidth_offset = p.bitwidth_offset
    bitwidth_dirty  = p.bitwidth_dirty

    @s.update
    def is_dirty_logic():
      if s.wd_en:
        # Check if the specific word is dirty
        s.is_dirty = s.dirty_bits[s.offset[2:bitwidth_offset]]
      else:
        s.is_dirty = b1(0)
        # OR all the wires together to see if a line is dirty
        for i in range( bitwidth_dirty ):
          if s.dirty_bits[i]:
            s.is_dirty = b1(1)

  def line_trace( s ):
    msg = ""
    msg += f"o:{s.is_dirty} m:{s.dirty_bits} "
    return msg

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
  Determines if cacheline is dirty
  """

  def construct( s, p ):
    s.is_hit     = InPort ( Bits1 )
    s.offset     = InPort ( BitsOffset)
    s.dirty_bits = InPort ( p.BitsDirty )
    s.is_dirty   = OutPort( Bits1 )

    @s.update
    def is_dirty_logic():
      if s.is_hit:
        s.is_dirty = s.dirty_bits[s.offset / 4]
      else:
        s.is_dirty = b1(0)
        for i in range( p.bitwidth_dirty ):
          if s.dirty_bits[i]:
            s.is_dirty = b1(1)

class DirtyBitWriter( Component ):
  """
  Writes dirty bit in Tag Array SRAM
  """

  def construct( s, p ):
    s.offset             = InPort ( p.BitsOffset )
    s.dirty_bits         = InPort ( p.BitsDirty )
    s.is_write_refill    = InPort ( Bits1 )
    s.is_write_hit_clean = InPort ( Bits1 )

    s.out                = OutPort( p.BitsDirty )

    @s.update
    def new_dirty_bit_logic():
      s.out = p.BitsDirty( 0 )
      if s.is_write_refill: 
        s.out[s.offset/4] = b1(1)
      elif s.is_write_hit_clean:
        s.out = s.dirty_bits
        s.out[s.offset/4] = b1(1)



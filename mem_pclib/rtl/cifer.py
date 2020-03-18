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
    s.is_hit     = InPort ( Bits1 )
    s.offset     = InPort ( p.BitsOffset)
    s.dirty_bits = InPort ( p.BitsDirty )
    s.is_dirty   = OutPort( Bits1 )

    bitwidth_offset = p.bitwidth_offset
    @s.update
    def is_dirty_logic():
      if s.is_hit:
        # Check if the specific word is dirty 
        s.is_dirty = s.dirty_bits[s.offset[2:bitwidth_offset]]
      else:
        s.is_dirty = b1(0)
        # OR all the wires together to see if a line is dirty
        for i in range( p.bitwidth_dirty ):
          if s.dirty_bits[i]:
            s.is_dirty = b1(1)
  
  def line_trace( s ):
    msg = ""
    msg += f"o:{s.is_dirty} mask:{s.dirty_bits} "
    return msg

class DirtyBitWriter( Component ):
  """
  Generates the dirty bit per word mask at the M0 stage to be written into 
  the Tag array SRAM
  """

  def construct( s, p ):
    s.offset             = InPort ( p.BitsOffset )
    s.dirty_bits         = [InPort ( p.BitsDirty ) for _ in range(p.associativity)]
    s.hit_way            = InPort ( p.BitsAssoclog2 )
    s.is_write_refill    = InPort ( Bits1 )
    s.is_write_hit_clean = InPort ( Bits1 )
    s.out                = OutPort( p.BitsDirty )

    bitwidth_offset = p.bitwidth_offset
    @s.update
    def new_dirty_bit_logic():
      s.out = p.BitsDirty( 0 )
      if s.is_write_refill: 
        s.out[s.offset[2:bitwidth_offset]] = b1(1)
      elif s.is_write_hit_clean:
        s.out = s.dirty_bits[s.hit_way]
        s.out[s.offset[2:bitwidth_offset]] = b1(1)

  def line_trace( s ):
    msg = ""
    msg += f"writer:{s.out} "
    return msg

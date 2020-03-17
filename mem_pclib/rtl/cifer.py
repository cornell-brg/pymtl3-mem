'''
=========================================================================
cifer.py
=========================================================================
Modules used in cifer project

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   17 March 2020
'''

from pymtl3 import *

class DirtyLineDetector( Component ):
  '''
  Determines if cacheline is dirty
  '''

  def construct( s, p ):

    s.dirty_bits = InPort ( p.BitsDirty )
    s.is_dirty   = OutPort( Bits1 )

    @s.update
    def is_dirty_logic():
      
      s.is_dirty = b1(0)

      for i in range( p.bitwidth_dirty ):
        if s.dirty_bits[i]:
          s.is_dirty = b1(1)



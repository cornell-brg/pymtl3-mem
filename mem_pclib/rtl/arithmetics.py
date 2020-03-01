"""
=========================================================================
arithmetic.py
=========================================================================
Combined arithmetic modules for the cache such as adders and multipliers

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

from pymtl3 import *

class EComp ( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_ecomp():
      s.out = Bits1(s.in0 == s.in1)

class Indexer ( Component ):

  def construct ( s, p ):
    s.index = InPort( p.BitsIdx )
    s.offset= InPort( p.BitsAssoclog2 )
    s.out   = OutPort( p.BitsClogNlines )
    @s.update
    def index_logic():
      s.out = p.BitsClogNlines(s.index) + p.BitsClogNlines(s.offset) * \
        p.BitsClogNlines(p.nblocks_per_way)

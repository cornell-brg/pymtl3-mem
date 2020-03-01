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
    BitsClogNlines  = p.BitsClogNlines
    nblocks_per_way = p.nblocks_per_way
    @s.update
    def index_logic():
      s.out = BitsClogNlines( s.index ) + BitsClogNlines( s.offset ) * \
        BitsClogNlines( nblocks_per_way )

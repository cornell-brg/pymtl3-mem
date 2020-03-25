"""
=========================================================================
arithmetic.py
=========================================================================
Combined arithmetic modules for the cache such as modified adders, 
multipliers and comparators

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

from mem_pclib.constants.constants   import *
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
    s.index  = InPort( p.BitsIdx )
    s.offset = InPort( p.BitsAssoclog2 )
    s.out    = OutPort( p.BitsClogNlines )
    BitsClogNlines  = p.BitsClogNlines
    nblocks_per_way = p.nblocks_per_way
    @s.update
    def index_logic(): 
      s.out = BitsClogNlines( s.index ) + BitsClogNlines( s.offset ) * \
        BitsClogNlines( nblocks_per_way )

class Comparator( Component ):

  def construct(s, p):
    s.addr_tag  = InPort(p.BitsTag)
    s.tag_array = [ InPort(p.StructTagCtrl) for _ in range(p.associativity) ]
    s.type_     = InPort( p.BitsType )
    s.hit       = OutPort(Bits1)
    s.hit_way   = OutPort(p.BitsAssoclog2)
    s.line_val  = OutPort( p.BitsAssoc )

    BitsAssoclog2 = p.BitsAssoclog2
    BitsAssoc = p.BitsAssoc
    associativity = p.associativity
    @s.update
    def comparing_logic():
      s.hit      = n
      s.hit_way  = BitsAssoclog2(0)
      s.line_val = BitsAssoc(0)
      if s.type_ == INIT:
        s.hit = n
      elif s.type_ >= AMO_ADD:
        for i in range( associativity ):
          if ( s.tag_array[i].val ):
            s.line_val[i] = y
        s.hit = n
      else:
        for i in range( associativity ):
          if ( s.tag_array[i].val ):
            s.line_val[i] = y
            if s.tag_array[i].tag == s.addr_tag:
              s.hit = y
              s.hit_way = BitsAssoclog2(i) 

"""
=========================================================================
arithmetic.py
=========================================================================
Combined arithmetic modules for the cache such as modified adders,
multipliers and comparators. Also include replicators

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

from pymtl3 import *

from constants.constants import *

class EComp ( Component ):

  def construct( s, Type ):

    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_ecomp():
      s.out = Bits1(s.in0 == s.in1)

class CacheDataReplicator( Component ):

  def construct( s , p ):

    s.msg_len = InPort ( p.BitsLen )
    s.data    = InPort ( p.BitsData )
    s.type_   = InPort ( p.BitsType )
    s.offset  = InPort ( p.BitsOffset )
    s.out     = OutPort( p.BitsCacheline )

    BitsLen            = p.BitsLen
    bitwidth_cacheline = p.bitwidth_cacheline
    bitwidth_data      = p.bitwidth_data
    BitsCacheline      = p.BitsCacheline
    BitsData           = p.BitsData
    bitwidth_offset    = p.bitwidth_offset
    s.mask = Wire(BitsCacheline)
    @s.update
    def replicator():
      if s.msg_len == BitsLen(1):
        for i in range( 0, bitwidth_cacheline, 8 ): # byte
          s.out[i:i+8] = s.data[0:8]
      elif s.msg_len == BitsLen(2):
        for i in range( 0, bitwidth_cacheline, 16 ): # half word
          s.out[i:i+16] = s.data[0:16]
      else:
        for i in range( 0, bitwidth_cacheline, bitwidth_data ):
          s.out[i:i+bitwidth_data] = s.data

      s.mask = BitsCacheline(0)
      if s.type_ >= AMO:
        ff = BitsData(-1)
        # AMO operations are word only. All arithmetic operations are based 2
        # so "multipliers" and "dividers" should be optimized to shifters
        s.mask = BitsCacheline(ff) << (b32(s.offset[2:bitwidth_offset]) * bitwidth_data)
        s.out  = s.mask & s.out

  def line_trace( s ):
    msg = ''
    msg += f'type:{s.type_} out:{s.out} '
    msg += f'mask:{s.mask} d:{(b32(s.offset) * 32 // 4)}'
    return msg

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

    s.addr_tag  = InPort( p.BitsTag )
    s.tag_array = [ InPort( p.StructTagArray ) for _ in range( p.associativity ) ]
    s.type_     = InPort ( p.BitsType )
    s.hit       = OutPort( Bits1 )
    s.hit_way   = OutPort( p.BitsAssoclog2 )
    s.line_val  = OutPort( p.BitsAssoc )

    BitsAssoclog2 = p.BitsAssoclog2
    BitsAssoc     = p.BitsAssoc
    associativity = p.associativity

    @s.update
    def comparing_logic():
      s.hit      = n
      s.hit_way  = BitsAssoclog2(0)
      s.line_val = BitsAssoc(0)
      if s.type_ == INIT:
        s.hit = n
      # elif s.type_ >= AMO_ADD:
      #   for i in range( associativity ):
      #     if ( s.tag_array[i].val ):
      #       s.line_val[i] = y
      #   s.hit = n
      else:
        for i in range( associativity ):
          if ( s.tag_array[i].val ):
            s.line_val[i] = y
            if s.tag_array[i].tag == s.addr_tag:
              s.hit = y
              s.hit_way = BitsAssoclog2(i)

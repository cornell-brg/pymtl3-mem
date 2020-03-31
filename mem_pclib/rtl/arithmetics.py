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
from mem_pclib.constants.constants   import *
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegEn

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
    s.offset  = InPort ( p.BitsOffset )
    s.is_amo  = InPort ( Bits1 )
    s.out     = OutPort( p.BitsCacheline )

    BitsLen            = p.BitsLen
    bitwidth_cacheline = p.bitwidth_cacheline
    bitwidth_data      = p.bitwidth_data
    BitsCacheline      = p.BitsCacheline
    BitsData           = p.BitsData
    bitwidth_offset    = p.bitwidth_offset
    @s.update
    def replicator_logic(): 
      if s.is_amo:
        s.out = BitsCacheline(0)
        s.out[0:bitwidth_data] = s.data
      else:
        if s.msg_len == BitsLen(1): 
          for i in range( 0, bitwidth_cacheline, 8 ): # byte
            s.out[i:i+8] = s.data[0:8]
        elif s.msg_len == BitsLen(2):
          for i in range( 0, bitwidth_cacheline, 16 ): # half word
            s.out[i:i+16] = s.data[0:16]
        else:
          for i in range( 0, bitwidth_cacheline, bitwidth_data ):
            s.out[i:i+bitwidth_data] = s.data

  def line_trace( s ):
    msg = ''
    msg += f'amo:{s.is_amo} out:{s.out} '
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
  
  def line_trace( s ):
    msg = ""
    msg = f"idx:{s.index} off:{s.offset} "
    return msg

class Comparator( Component ):

  def construct(s, p):

    s.addr_tag  = InPort( p.BitsTag )
    s.tag_array = [ InPort( p.StructTagArray ) for _ in range( p.associativity ) ]
    s.is_init   = InPort ( Bits1 )
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
      if s.is_init:
        s.hit = n
      else:
        for i in range( associativity ):
          if ( s.tag_array[i].val ):
            s.line_val[i] = y
            if s.tag_array[i].tag == s.addr_tag:
              s.hit = y
              s.hit_way = BitsAssoclog2(i)
    
  def line_trace( s ):
    msg = ''
    msg += f'hit:{s.hit} hit_way:{s.hit_way} '
    return msg

class OffsetLenSelector( Component ):

  def construct(s, p):
    s.offset_i = InPort( p.BitsOffset )
    s.is_amo  = InPort ( Bits1 )
    s.offset_o = OutPort( p.BitsOffset )
    s.len      = OutPort( p.BitsMemLen )

    BitsOffset = p.BitsOffset 
    BitsMemLen = p.BitsMemLen
    bitwidth_data = p.bitwidth_data
    @s.update
    def offset_selection_logic():
      if s.is_amo:
        s.offset_o = s.offset_i
        s.len = BitsMemLen( bitwidth_data >> 3 )
      else:
        s.offset_o = BitsOffset(0)
        s.len = BitsMemLen(0)

class WriteMaskSelector( Component ):
  """
  Sets the write mask for the memreq based on the type of transactions in flight
  """
  def construct(s, p):
    s.in_    = InPort( p.BitsDirty )     # M1 stage
    s.out    = OutPort( p.BitsDirty )    # M2 stage
    s.is_amo = InPort(Bits1)
    s.offset = InPort( p.BitsOffset ) # M2 stage 
    s.en     = InPort( Bits1 )

    s.write_mask = RegEnRst( p.BitsDirty )(
      in_ = s.in_,
      en  = s.en
    )
    BitsDirty = p.BitsDirty
    bitwidth_offset = p.bitwidth_offset
    
    @s.update
    def write_mask_selection_logic():
      if s.is_amo:
        s.out = BitsDirty(1) << (b32(s.offset[2:bitwidth_offset]))
      else:  
        s.out = s.write_mask.out
  
  def line_trace( s ):
    msg = ''
    msg += f'in_:{s.in_} out:{s.out} amo:{s.is_amo} dirty_nbits:{s.in_.nbits}'
    return msg

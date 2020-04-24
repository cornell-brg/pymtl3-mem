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
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegEn

from constants.constants import *
from ..constants import *

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

    s.in_    = InPort ( p.BitsData )
    s.len_   = InPort ( p.BitsLen )
    s.offset = InPort ( p.BitsOffset )
    s.amo    = InPort ( Bits1 )
    s.out    = OutPort( p.BitsCacheline )

    BitsLen            = p.BitsLen
    bitwidth_cacheline = p.bitwidth_cacheline
    bitwidth_data      = p.bitwidth_data
    BitsCacheline      = p.BitsCacheline
    BitsData           = p.BitsData
    bitwidth_offset    = p.bitwidth_offset
    @s.update
    def replicator_logic(): 
      if s.amo:
        s.out = BitsCacheline(0)
        s.out[0:bitwidth_data] = s.in_
      else:
        if s.len_ == BitsLen(1): 
          for i in range( 0, bitwidth_cacheline, 8 ): # byte
            s.out[i:i+8] = s.in_[0:8]
        elif s.len_ == BitsLen(2):
          for i in range( 0, bitwidth_cacheline, 16 ): # half word
            s.out[i:i+16] = s.in_[0:16]
        else:
          for i in range( 0, bitwidth_cacheline, bitwidth_data ):
            s.out[i:i+bitwidth_data] = s.in_

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
    
    s.dirty_line = InPort( p.BitsAssoc )
    s.inval_hit  = OutPort( Bits1 )

    BitsAssoclog2 = p.BitsAssoclog2
    BitsAssoc     = p.BitsAssoc
    associativity = p.associativity

    @s.update
    def comparing_logic():
      s.hit       = n
      s.inval_hit = n
      s.hit_way   = BitsAssoclog2(0)
      if not s.is_init:
        for i in range( associativity ):
          if s.tag_array[i].val == CACHE_LINE_STATE_VALID:
            if s.tag_array[i].tag == s.addr_tag:
              s.hit = y
              s.hit_way = BitsAssoclog2(i)
          elif s.dirty_line[i]:
            # If not valid, then we check if the line is dirty at all 
            # If its dirty, then we flag the transaction as an access to a 
            # partially dirty line that may require special attention
            if s.tag_array[i].tag == s.addr_tag:
              s.inval_hit = y
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

class TagArrayRDataProcessUnit( Component ):

  def construct(s, p):

    s.addr_tag  = InPort( p.BitsTag )
    s.tag_array = [ InPort( p.StructTagArray ) for _ in range( p.associativity ) ]
    s.is_init   = InPort ( Bits1 )
    s.hit_way   = OutPort( p.BitsAssoclog2 )
    s.hit       = OutPort( Bits1 ) # general hit
    s.inval_hit = OutPort( Bits1 ) # hit on an invalid cache line that is dirty
    
    s.offset    = InPort( p.BitsOffset )
    s.word_dirty= OutPort( p.BitsAssoc ) # If the word in cacheline is dirty
    s.line_dirty= OutPort( p.BitsAssoc ) # If the line is dirty

    BitsAssoclog2 = p.BitsAssoclog2
    BitsAssoc     = p.BitsAssoc
    associativity = p.associativity
    bitwidth_offset = p.bitwidth_offset
    bitwidth_dirty  = p.bitwidth_dirty

    # word dirty logic
    for i in range( associativity ):
      s.word_dirty[i] //= lambda: s.tag_array[i].dty[s.offset[2:bitwidth_offset]]

    @s.update
    def line_dirty_logic():
      s.line_dirty = BitsAssoc( 0 )
      # OR all the wires together to see if a line is dirty
      for i in range( associativity ):
        for j in range( bitwidth_dirty ):
          if s.tag_array[i].dty[j]:
            s.line_dirty[i] = y

    @s.update
    def comparing_logic():
      s.hit       = n
      s.inval_hit = n
      s.hit_way   = BitsAssoclog2(0)
      if not s.is_init:
        for i in range( associativity ):
          if s.tag_array[i].val == CACHE_LINE_STATE_VALID:
            if s.tag_array[i].tag == s.addr_tag:
              s.hit      = s.hit | y
              s.hit_way  = BitsAssoclog2(i)
          if s.line_dirty[i] & (s.tag_array[i].val == CACHE_LINE_STATE_INVALID):
            # If not valid, then we check if the line is dirty at all 
            # If its dirty, then we flag the transaction as an access to a 
            # partially dirty line that may require special attention
            if s.tag_array[i].tag == s.addr_tag:
              s.inval_hit = s.hit | y
              s.hit_way   = BitsAssoclog2(i)
    
  def line_trace( s ):
    msg = ''
    msg += f'hit:{s.hit} hit_way:{s.hit_way} inv_hit:{s.inval_hit} '
    return msg

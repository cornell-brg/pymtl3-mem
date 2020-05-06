'''
=========================================================================
Muxes.py
=========================================================================
Data select mux: selects the byte accesses of the mux

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   27 February 2020
'''

from pymtl3 import *
from pymtl3.stdlib.rtl.arithmetics import Mux

class OptimizedMux( Component ):
  '''Optimized 2 input muxes'''
  def construct( s, Type, ninputs ):
    s.in_ = [ InPort( Type ) for _ in range(ninputs) ]
    s.sel = InPort( max(1, clog2(ninputs)) )
    s.out = OutPort( Type )

    if ninputs == 2:
      s.out //= lambda: s.in_[1] if s.sel else s.in_[0]
    else:
      s.mux = Mux( Type, ninputs )
      for i in range( ninputs ):
        s.mux.in_[i] //= s.in_[i]
      s.mux.sel //= s.sel
      s.mux.out //= s.out

class SubInputMux( Component ):
  '''
  Selects the correct way and zero extends 
  '''
  def construct( s, bitwidth_mux, bitwidth_data ):
    BitsMux   = mk_bits( bitwidth_mux )
    BitsData  = mk_bits( bitwidth_data )
    
    s.in_ = InPort( BitsData )
    s.out = OutPort( BitsData )
    s.sel = InPort()

    s.mux = m = Mux( BitsMux, 2 )
    m.sel //= s.sel
    m.in_[0] //= s.in_[ 0 : bitwidth_mux ]
    m.in_[1] //= s.in_[ bitwidth_mux : bitwidth_mux * 2 ]

    if bitwidth_mux < bitwidth_data:
      s.out[ bitwidth_mux : bitwidth_data ] //= 0
    s.out[ 0 : bitwidth_mux ] //= s.mux.out
  
  def line_trace( s ):
    msg = f'o[{s.out}] i1[{s.mux.in_[0]}] i2[{s.mux.in_[1]}]'
    return msg

class DataSelectMux( Component ):

  def construct( s, p ):
    s.in_    = InPort( p.BitsCacheline )
    s.out    = OutPort( p.BitsData )
    s.en     = InPort()
    s.amo    = InPort()
    s.len_   = InPort( p.BitsLen )
    s.offset = InPort( p.BitsOffset )
    
    nmuxes = clog2( p.bitwidth_cacheline // 8 )

    sub = []
    for i in range( 3, clog2( p.bitwidth_cacheline ) ):
      sub.append( SubInputMux( 2**i, p.bitwidth_cacheline ) )
    s.sub = sub
    for i in range( 1, nmuxes ):
      s.sub[i-1].in_ //= s.sub[i].out
    s.sub[nmuxes-1].in_ //= s.in_

    for i in range( nmuxes ):
      s.sub[i].sel //= lambda : s.en & s.offset[i]

    ninputs = clog2( p.bitwidth_data ) 
    s.output_mux = m = Mux( p.BitsData, ninputs )
    m.in_[0] //= p.BitsData(0)
    m.in_[1] //= s.in_[ 0 : p.bitwidth_data ] # AMO operations
    for i in range( ninputs - 2 ):
      if i < nmuxes:
        m.in_[i+2] //= s.sub[i].out[ 0 : p.bitwidth_data ]
      else:
        m.in_[i+2] //= s.in_[ 0 : p.bitwidth_data ]

    BitsSel = mk_bits( clog2(ninputs) )
    BitsLen = p.BitsLen
    @s.update
    def output_mux_selection_logic():
      s.output_mux.sel @= BitsSel(0)
      if s.amo:
        s.output_mux.sel @= BitsSel(1)
      elif ~s.en:
        s.output_mux.sel @= BitsSel(0)
      else:
        for i in range( ninputs - 2 ):
          if s.len_ == BitsLen(2**i, trunc_int=True):
            s.output_mux.sel @= BitsSel(i+2)
    s.out //= s.output_mux.out

  def line_trace( s ):
    msg = f'i[{s.in_}] o[{s.out}] s[{s.output_mux.sel}] '
    # msg += f'{s.output_mux.in_} '
    # msg += f's2o[{s.sub[2].out}]'
    return msg

class SubInputMux2( Component ):
  def construct( s, bitwidth_mux, p ):
    BitsMux = mk_bits( bitwidth_mux )
    
    s.in_ = InPort( p.BitsCacheline )
    s.out = OutPort( p.BitsData )
    s.sel = InPort( p.BitsOffset )

    ninputs = p.bitwidth_cacheline // bitwidth_mux
    s.mux = m = Mux( BitsMux, ninputs )
    for i in range( ninputs ):
      m.in_[i] //= s.in_[ i * bitwidth_mux : (i + 1) * bitwidth_mux ]
    
    s.out[0:bitwidth_mux] //= s.mux.out[0:bitwidth_mux]
    if bitwidth_mux < p.bitwidth_data:
      s.out[bitwidth_mux:p.bitwidth_data] //= 0

    BitsSel = clog2( ninputs )
    s.mux.sel //= s.sel[ clog2(bitwidth_mux) - 3 : p.bitwidth_offset ]

class FastDataSelectMux( Component ):
  """faster version in case the other DataSelectMux doesn't meet timing"""
  def construct( s, p ):
    s.in_    = InPort( p.BitsCacheline )
    s.out    = OutPort( p.BitsData )
    s.en     = InPort()
    s.amo    = InPort()
    s.len_   = InPort( p.BitsLen )
    s.offset = InPort( p.BitsOffset )

    if p.bitwidth_cacheline > p.bitwidth_data:
      # need mux for data bitwidth as well but don't need any higher
      nmuxes = clog2( p.bitwidth_data ) - 2
    elif p.bitwidth_cacheline == p.bitwidth_data:
      # don't count the mux for when data = cacheline bitwidth
      nmuxes = clog2( p.bitwidth_data ) - 3 

    s.mux_blocks = [SubInputMux2( 2**i, p ) for i in range( 3, 3 + nmuxes )]
    # instanitate the mux blocks that will select the subwords
    for i, m in enumerate( s.mux_blocks ):
      m.in_ //= s.in_
      m.sel //= s.offset

    ninputs = clog2( p.bitwidth_data ) 
    s.output_mux = m = Mux( p.BitsData, ninputs )
    m.in_[0] //= 0
    m.in_[1][0:32] //= s.in_[0:32] #AMO always 32 bit access?
    if p.bitwidth_data > 32:
      m.in_[1][32:p.bitwidth_data] //= 0 
    for i in range( ninputs - 2 ):
      if i < nmuxes:
        m.in_[i+2] //= s.mux_blocks[i].out[0:p.bitwidth_data]
      else:
        m.in_[i+2] //= s.in_[ 0 : p.bitwidth_data ]
    
    BitsSel = mk_bits( clog2(ninputs) )
    BitsLen = p.BitsLen
    @update
    def output_mux_selection_logic():
      s.output_mux.sel @= BitsSel(0)
      if s.amo:
        s.output_mux.sel @= BitsSel(1)
      elif ~s.en:
        s.output_mux.sel @= BitsSel(0)
      else:
        for i in range( ninputs - 2 ):
          if s.len_ == BitsLen(2**i, trunc_int=True):
            s.output_mux.sel @= BitsSel(i+2)
    s.out //= s.output_mux.out

  def line_trace( s ):
    msg = ''
    msg = f'i[{s.in_}] o[{s.out}] s[{s.output_mux.sel}] '
    msg += f'{s.output_mux.in_} '
    # msg += f's2o[{s.sub[2].out}]'
    return msg

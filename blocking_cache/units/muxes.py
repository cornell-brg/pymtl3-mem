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

class DataSizeMux( Component ):
  '''
  This mux allows for byte, 2 byte or word data access (4 bytes)
  depending on the len type.
  '''

  def construct( s, p ):

    s.data   = InPort( p.BitsCacheline )
    s.en     = InPort( Bits1 )
    s.len_   = InPort( p.BitsLen )
    s.offset = InPort( p.BitsOffset )
    s.out    = OutPort( p.BitsData )
    s.is_amo = InPort( Bits1 )

    s.read_data_mux_sel      = Wire(p.BitsRdDataMuxSel)
#    s.read_word_mux_sel      = Wire(p.BitsRdWordMuxSel)
    s.read_2byte_mux_sel     = Wire(p.BitsRd2ByteMuxSel)
    s.read_byte_mux_sel      = Wire(p.BitsRdByteMuxSel)
    s.subword_access_mux_sel = Wire(Bits2)

    s.read_amo = Wire(p.BitsData)
    if p.bitwidth_data > 32:
      s.read_amo[32:p.bitwidth_data] //= 0
    s.read_amo[0:32] //= s.data[0:32]
    
    # Data select mux
    s.read_data_mux = Mux(p.BitsData, p.bitwidth_cacheline // p.bitwidth_data \
      + 1)(
      sel = s.read_data_mux_sel
    )
    s.read_data_mux.in_[0] //= p.BitsData(0)
    for i in range(1, p.bitwidth_cacheline//p.bitwidth_data+1):
      s.read_data_mux.in_[i] //= s.data[(i - 1) * p.bitwidth_data:i * p.bitwidth_data]

    # Word byte select mux NOT USED YET
#    s.read_word_mux = Mux(Bits32, p.bitwidth_data//32)(
#      sel = s.read_word_mux_sel
#    )
#    for i in range(p.bitwidth_data//32):
#      s.read_word_mux.in_[i] //= s.read_data_mux.out[i * 32:(i + 1) * 32]
#
#    s.read_word_zero_extended = Wire(p.BitsData)
#    if p.bitwidth_data > 32:
#      s.read_word_zero_extended[32:p.bitwidth_data] //= 0
#    s.read_word_zero_extended[0:32] //= s.read_word_mux.out

    # Two byte select mux
    s.read_2byte_mux = Mux(Bits16, p.bitwidth_data//16)(
      sel = s.read_2byte_mux_sel
    )
    for i in range(p.bitwidth_data//16):
      s.read_2byte_mux.in_[i] //= s.read_data_mux.out[i * 16:(i + 1) * 16]

    s.read_2byte_zero_extended = Wire(p.BitsData)
    s.read_2byte_zero_extended[16:p.bitwidth_data] //= 0
    s.read_2byte_zero_extended[0:16] //= s.read_2byte_mux.out

    # Byte select mux
    s.read_byte_mux = Mux(Bits8, p.bitwidth_data//8)(
      sel = s.read_byte_mux_sel
    )
    for i in range(p.bitwidth_data//8):
      s.read_byte_mux.in_[i] //= s.read_data_mux.out[i * 8:(i + 1) * 8]

    s.read_byte_zero_extended = Wire(p.BitsData)
    s.read_byte_zero_extended[8:p.bitwidth_data] //= 0
    s.read_byte_zero_extended[0:8] //= s.read_byte_mux.out

    # Datasize Mux
    s.subword_access_mux = Mux(p.BitsData, 3)(
      in_ = {
        0: s.read_data_mux.out,
        1: s.read_byte_zero_extended,
        2: s.read_2byte_zero_extended
      },
      sel = s.subword_access_mux_sel,
    )

    ## Ctrl logic
    BitsRdDataMuxSel = p.BitsRdDataMuxSel
    btmx0   = p.BitsRdByteMuxSel(0)
    bbmx0   = p.BitsRd2ByteMuxSel(0)
#    wwmx0   = p.BitsRdWordMuxSel(0)
    wdmx0   = p.BitsRdDataMuxSel(0)
    acmx0   = Bits2(0)
    offset  = p.bitwidth_offset
    BitsLen = p.BitsLen
    bitwidth_data = p.bitwidth_data
    @s.update
    def subword_access_mux_sel_logic():
      s.read_byte_mux_sel      = btmx0
      s.read_2byte_mux_sel     = bbmx0
#      s.read_word_mux_sel      = wwmx0
      s.read_data_mux_sel      = wdmx0
      s.subword_access_mux_sel = acmx0
      if s.en:
        s.read_data_mux_sel = BitsRdDataMuxSel(s.offset[2:offset]) + BitsRdDataMuxSel(1)
        if s.len_ == BitsLen(1):
          s.read_byte_mux_sel      = s.offset[0:2]
          s.subword_access_mux_sel = Bits2(1)
        elif s.len_ == BitsLen(2):
          s.read_2byte_mux_sel     = s.offset[1:2]
          s.subword_access_mux_sel = Bits2(2)
      
      if s.is_amo:
        s.out = s.read_amo
      else:
        s.out = s.subword_access_mux.out


class PMux( Component ):
  '''
  N-input Mux that allows for ninputs = 1
  '''

  def construct( s, Type, ninputs ):
    BitsSel = Bits1 if ninputs <= 1 else mk_bits( clog2(ninputs) )
    s.in_ = [ InPort( Type ) for _ in range(ninputs) ]
    s.out = OutPort( Type )
    s.sel = InPort( BitsSel )

    @s.update
    def up_mux():
      s.out = s.in_[ s.sel ]

  def line_trace( s ):
    msg = ''
    for i in range(len(s.in_)):
      msg += f'i{i}:{s.in_[i]} '
    return msg + f'o:{s.out} '


class SubInputMux( Component ):
  '''
  Selects the correct way and zero extends 
  '''
  def construct( s, bitwidth_mux, bitwidth_data ):
    BitsMux   = mk_bits( bitwidth_mux )
    BitsData  = mk_bits( bitwidth_data )
    
    s.in_    = InPort( BitsData )
    s.out    = OutPort( BitsData )
    s.sel    = InPort( Bits1 )

    s.mux = Mux( BitsMux, 2 )
    s.mux.sel //= s.sel
    s.mux.in_[0] //= s.in_[ 0 : bitwidth_mux ]
    s.mux.in_[1] //= s.in_[ bitwidth_mux : bitwidth_mux * 2 ]

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
    s.en     = InPort( Bits1 )
    s.amo    = InPort( Bits1 )
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
    s.output_mux = Mux( p.BitsData, ninputs )
    s.output_mux.in_[0] //= p.BitsData(0)
    s.output_mux.in_[1] //= s.in_[ 0 : p.bitwidth_data ] # AMO operations
    for i in range( ninputs - 2 ):
      if i < nmuxes:
        s.output_mux.in_[i+2] //= s.sub[i].out[ 0 : p.bitwidth_data ]
      else:
        s.output_mux.in_[i+2] //= s.in_[ 0 : p.bitwidth_data ]

    BitsSel = mk_bits( clog2(ninputs) )
    BitsLen = p.BitsLen
    @s.update
    def output_mux_selection_logic():
      s.output_mux.sel = BitsSel(0)
      if s.amo:
        s.output_mux.sel = BitsSel(1)
      elif ~s.en:
        s.output_mux.sel = BitsSel(0)
      else:
        for i in range( ninputs - 2 ):
          if s.len_ == BitsLen(2**i):
            s.output_mux.sel = BitsSel(i+2)
    s.out //= s.output_mux.out

  def line_trace( s ):
    msg = f'i[{s.in_}] o[{s.out}] s[{s.output_mux.sel}] '
    # msg += f'{s.output_mux.in_} '
    # msg += f's2o[{s.sub[2].out}]'
    return msg

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

    s.read_word_mux_sel      = Wire(p.BitsRdWordMuxSel)
    s.read_2byte_mux_sel     = Wire(p.BitsRd2ByteMuxSel)
    s.read_byte_mux_sel      = Wire(p.BitsRdByteMuxSel)
    s.subword_access_mux_sel = Wire(Bits2)
    # Word select mux
    s.read_word_mux = Mux(p.BitsData, p.bitwidth_cacheline // p.bitwidth_data \
      + 1)(
      sel = s.read_word_mux_sel
    )
    s.read_word_mux.in_[0] //= p.BitsData(0)
    for i in range(1, p.bitwidth_cacheline//p.bitwidth_data+1):
      s.read_word_mux.in_[i] //= s.data[(i - 1) * p.bitwidth_data:i * p.bitwidth_data]

    # Two byte select mux
    s.read_2byte_mux = Mux(Bits16, p.bitwidth_data//16)(
      sel = s.read_2byte_mux_sel
    )
    for i in range(p.bitwidth_data//16):
      s.read_2byte_mux.in_[i] //= s.read_word_mux.out[i * 16:(i + 1) * 16]

    s.read_2byte_zero_extended = Wire(p.BitsData)
    s.read_2byte_zero_extended[16:p.bitwidth_data] //= 0
    s.read_2byte_zero_extended[0:16] //= s.read_2byte_mux.out

    # Byte select mux
    s.read_byte_mux = Mux(Bits8, p.bitwidth_data//8)(
      sel = s.read_byte_mux_sel
    )
    for i in range(p.bitwidth_data//8):
      s.read_byte_mux.in_[i] //= s.read_word_mux.out[i * 8:(i + 1) * 8]

    s.read_byte_zero_extended = Wire(p.BitsData)
    s.read_byte_zero_extended[8:p.bitwidth_data] //= 0
    s.read_byte_zero_extended[0:8] //= s.read_byte_mux.out

    # Datasize Mux
    s.subword_access_mux = Mux(p.BitsData, 3)(
      in_ = {
        0: s.read_word_mux.out,
        1: s.read_byte_zero_extended,
        2: s.read_2byte_zero_extended
      },
      sel = s.subword_access_mux_sel,
    )

    ## Ctrl logic
    BitsRdWordMuxSel = p.BitsRdWordMuxSel
    btmx0   = p.BitsRdByteMuxSel(0)
    bbmx0   = p.BitsRd2ByteMuxSel(0)
    acmx0   = Bits2(0)
    wdmx0   = p.BitsRdWordMuxSel(0)
    offset  = p.bitwidth_offset
    BitsLen = p.BitsLen
    bitwidth_data = p.bitwidth_data
    @s.update
    def subword_access_mux_sel_logic():
      s.read_byte_mux_sel      = btmx0
      s.read_2byte_mux_sel     = bbmx0
      s.subword_access_mux_sel = acmx0
      s.read_word_mux_sel      = wdmx0
      if s.en:
        s.read_word_mux_sel = BitsRdWordMuxSel(s.offset[2:offset]) + BitsRdWordMuxSel(1)
        if s.len_ == BitsLen(1):
          s.read_byte_mux_sel      = s.offset[0:2]
          s.subword_access_mux_sel = Bits2(1)
        elif s.len_ == BitsLen(2):
          s.read_2byte_mux_sel     = s.offset[1:2]
          s.subword_access_mux_sel = Bits2(2)
      
      if s.is_amo:
        s.out = s.data[0:bitwidth_data]
      else:
        s.out = s.subword_access_mux.out


class PMux( Component ):
  '''
  N-input Mux that allows for ninputs = 1
  '''

  def construct( s, Type, ninputs ):
    BitsSel = Bits1 if ninputs == 1 else mk_bits( clog2(ninputs) )
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

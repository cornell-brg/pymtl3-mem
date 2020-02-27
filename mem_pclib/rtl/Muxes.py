'''
=========================================================================
Muxes.py
=========================================================================
Special muxes that are used throughout pymtl3-mem

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   27 February 2020
'''

from pymtl3 import *
from pymtl3.stdlib.rtl.arithmetics  import Mux

class DataSizeMux( Component ):
  '''
  This mux allows for byte, half-word or word data access
  '''

  def construct( s, p ):

    s.data              = InPort(p.BitsCacheline)
    s.word_mux_sel      = InPort(p.BitsRdWordMuxSel)
    s.half_word_mux_sel = InPort(p.BitsRd2ByteMuxSel)
    s.byte_mux_sel      = InPort(p.BitsRdByteMuxSel)
    s.data_size_mux_sel = InPort(Bits2)

    s.out               = OutPort(p.BitsData)

    # Word select mux 
    s.read_word_mux = Mux(p.BitsData, p.bitwidth_cacheline // p.bitwidth_data + 1)\
    (
      sel = s.word_mux_sel
    )
    s.read_word_mux.in_[0] //= p.BitsData(0) 
    for i in range(1, p.bitwidth_cacheline//p.bitwidth_data+1):
      s.read_word_mux.in_[i] //= s.data[(i - 1) * p.bitwidth_data:i * p.bitwidth_data]
        
    # Two byte select mux
    s.read_half_word_mux = Mux(Bits16, p.bitwidth_data//16)(
      sel = s.half_word_mux_sel 
    )
    for i in range(p.bitwidth_data//16):
      s.read_half_word_mux.in_[i] //= s.read_word_mux.out[i * 16:(i + 1) * 16]

    s.half_word_read_zero_extended = Wire(p.BitsData)
    s.half_word_read_zero_extended[16:p.bitwidth_data] //= 0
    s.half_word_read_zero_extended[0:16] //= s.read_half_word_mux.out

    # Byte select mux
    s.read_byte_mux = Mux(Bits8, p.bitwidth_data//8)(
      sel = s.byte_mux_sel
    )
    for i in range(p.bitwidth_data//8):
      s.read_byte_mux.in_[i] //= s.read_word_mux.out[i * 8:(i + 1) * 8]

    s.byte_read_zero_extended = Wire(p.BitsData)
    s.byte_read_zero_extended[8:p.bitwidth_data] //= 0
    s.byte_read_zero_extended[0:8] //= s.read_byte_mux.out

    # Datasize Mux
    s.subword_access_mux = Mux(p.BitsData, 3)(
      in_ = {
        0: s.read_word_mux.out,
        1: s.byte_read_zero_extended,
        2: s.half_word_read_zero_extended
      },
      sel = s.data_size_mux_sel,
    )

    s.out //= s.subword_access_mux.out


class PMux( Component ):
  '''
  N-input Mux that allows for ninputs = 1
  '''
  
  def construct( s, Type, ninputs ):

    s.in_ = [ InPort( Type ) for _ in range(ninputs) ]
    s.out = OutPort( Type )

    if ninputs > 1:
      s.sel = InPort( int if Type is int else mk_bits( clog2(ninputs) ) )
      @s.update
      def up_mux():
        s.out = s.in_[ s.sel ]

    else:
      s.sel = InPort ( Bits1 )
      @s.update
      def up_mux():
        s.out = s.in_[ b1(0) ]
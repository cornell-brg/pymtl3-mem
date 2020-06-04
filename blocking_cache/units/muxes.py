'''
=========================================================================
Muxes.py
=========================================================================
Data select mux: selects the byte accesses of the mux

Author: Eric Tang (et396), Xiaoyu Yan (xy97)
Date:   27 February 2020
'''

from pymtl3 import *
from pymtl3.stdlib.basic_rtl import Mux

class SubInputMux( Component ):
  """
  Submodule called by DataSelectMux
  Selects the correct way and zero extends 
  """
  def construct( s, bitwidth_mux, bitwidth_data ):
    s.in_ = InPort(bitwidth_data)
    s.out = OutPort(bitwidth_data)
    s.sel = InPort()

    s.mux = m = Mux(bitwidth_mux, 2)
    m.sel    //= s.sel
    m.in_[0] //= s.in_[0 : bitwidth_mux]
    m.in_[1] //= s.in_[bitwidth_mux : bitwidth_mux * 2]

    if bitwidth_mux < bitwidth_data:
      s.out[bitwidth_mux : bitwidth_data] //= 0
    s.out[0 : bitwidth_mux] //= s.mux.out
  
  def line_trace( s ):
    msg = f'o[{s.out}] i1[{s.mux.in_[0]}] i2[{s.mux.in_[1]}]'
    return msg

class DataSelectMux( Component ):
  """
  Selects the data from the output from the data array.
  
  Chains the muxes together with decreasing byte size. Slower

  The chains looks like this:
   in_
    |
  128-bit -> 64-bit -> 32-bit -> 16-bit -> 8-bit 
    |         |         |         |        |
    _________________________________________
    \__________________mux__________________/
                        |
                       out
  Critical path goes through 6 muxes
  """
  def construct( s, p ):
    s.in_    = InPort(p.bitwidth_cacheline)
    s.out    = OutPort(p.bitwidth_data)
    s.en     = InPort()
    s.amo    = InPort()
    s.len_   = InPort(p.bitwidth_len)
    s.offset = InPort(p.bitwidth_offset)
    
    nmuxes = clog2( p.bitwidth_cacheline // 8 )

    # number of 2 to 1 muxes
    sub = [] 
    for i in range( 3, clog2(p.bitwidth_cacheline) ):
      sub.append( SubInputMux(2**i, p.bitwidth_cacheline) )
    s.sub = sub
    # Connect the muxes in a chain
    for i in range(1, nmuxes):
      s.sub[i-1].in_ //= s.sub[i].out
    s.sub[nmuxes-1].in_ //= s.in_

    # Select for each mux depends on a specific bit in the offset
    for i in range(nmuxes):
      s.sub[i].sel //= lambda : s.en & s.offset[i]

    ninputs = clog2(p.bitwidth_data) 
    s.output_mux = m = Mux(p.bitwidth_data, ninputs)
    m.in_[0] //= 0 # output 0 for write/inv/flush requests
    m.in_[1] //= s.in_[0 : p.bitwidth_data] # AMO operations
    for i in range(ninputs - 2):
      if i < nmuxes:
        m.in_[i+2] //= s.sub[i].out[0 : p.bitwidth_data]
      else:
        m.in_[i+2] //= s.in_[0 : p.bitwidth_data]

    BitsSel = mk_bits( clog2(ninputs) )
    @update
    def output_mux_selection_logic():
      s.output_mux.sel @= 0
      if s.amo:
        s.output_mux.sel @= 1
      elif ~s.en:
        s.output_mux.sel @= 0
      else:
        if s.len_ == 0:
          s.output_mux.sel @= ninputs - 1  
        else:
          for i in range(ninputs - 3):
            if s.len_ == 2**i:
              s.output_mux.sel @= BitsSel(i) + 2
    s.out //= s.output_mux.out

  def line_trace( s ):
    msg = f'i[{s.in_}] o[{s.out}] s[{s.output_mux.sel}] '
    # msg += f'{s.output_mux.in_} '
    return msg

class FastSubInputMux( Component ):
  """
  Muxes for the faster data selector
  N input mux depending on the byte access
  """
  def construct( s, bitwidth_mux, p ):
    s.in_ = InPort(p.bitwidth_cacheline)
    s.out = OutPort(p.bitwidth_data)
    s.sel = InPort(p.bitwidth_offset)

    ninputs = p.bitwidth_cacheline // bitwidth_mux
    s.mux = m = Mux(bitwidth_mux, ninputs)
    for i in range(ninputs):
      m.in_[i] //= s.in_[i * bitwidth_mux : (i + 1) * bitwidth_mux]
    
    s.out[0 : bitwidth_mux] //= s.mux.out[0 : bitwidth_mux]
    if bitwidth_mux < p.bitwidth_data:
      s.out[bitwidth_mux : p.bitwidth_data] //= 0

    s.mux.sel //= s.sel[clog2(bitwidth_mux) - 3 : p.bitwidth_offset]

class FastDataSelectMux( Component ):
  """
  Faster version in case the other DataSelectMux doesn't meet timing
                     in_
                      |
      ________________________________ 
     |        |       |       |       |
  _______  ______  ______  ______   _____
  \_128_/  \_64_/  \_32_/  \_16_/   \_8_/
     |        |       |       |       |
   _____________________________________
   \___________________________________/
                    |
                   out
  All accesses have a different N-to-1 mux depending on byte access len_
  ex: 1 byte access with a 16 byte cacheline will need a 16-to-1 mux 
  """
  def construct( s, p ):
    s.in_    = InPort(p.bitwidth_cacheline)
    s.out    = OutPort(p.bitwidth_data)
    s.en     = InPort()
    s.amo    = InPort()
    s.len_   = InPort(p.bitwidth_len)
    s.offset = InPort(p.bitwidth_offset)

    if p.bitwidth_cacheline > p.bitwidth_data:
      # need mux for data bitwidth as well but don't need any higher
      nmuxes = clog2(p.bitwidth_data) - 2
    elif p.bitwidth_cacheline == p.bitwidth_data:
      # don't count the mux for when data = cacheline bitwidth
      nmuxes = clog2(p.bitwidth_data) - 3 

    s.mux_blocks = [FastSubInputMux(2**i, p) for i in range(3, 3 + nmuxes)]
    # instanitate the mux blocks that will select the subwords
    for i, m in enumerate(s.mux_blocks):
      m.in_ //= s.in_
      m.sel //= s.offset

    ninputs = clog2(p.bitwidth_data) 
    s.output_mux = m = Mux(p.bitwidth_data, ninputs)
    m.in_[0] //= 0
    m.in_[1][0:32] //= s.in_[0:32] #AMO always 32 bit access?
    if p.bitwidth_data > 32:
      m.in_[1][32 : p.bitwidth_data] //= 0 
    for i in range(ninputs - 2):
      if i < nmuxes:
        m.in_[i+2] //= s.mux_blocks[i].out[0 : p.bitwidth_data]
      else:
        m.in_[i+2] //= s.in_[0 : p.bitwidth_data]
    
    BitsSel = mk_bits( clog2(ninputs) )
    @update
    def output_mux_selection_logic():
      s.output_mux.sel @= 0
      if s.amo:
        s.output_mux.sel @= 1
      elif ~s.en:
        s.output_mux.sel @= 0
      else:
        if s.len_ == 0:
          s.output_mux.sel @= ninputs - 1  
        else:
          for i in range(ninputs - 3):
            if s.len_ == 2**i:
              s.output_mux.sel @= BitsSel(i) + 2
    s.out //= s.output_mux.out

  def line_trace( s ):
    msg = ''
    msg = f'i[{s.in_}] o[{s.out}] s[{s.output_mux.sel}] '
    msg += f'{s.output_mux.in_} '
    return msg

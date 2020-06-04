"""
=========================================================================
 registers.py
=========================================================================
Our own version of registers that handles bitstructs better

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""
from pymtl3                  import *
from pymtl3.stdlib.basic_rtl import RegEnRst, RegEn, RegRst

class ReplacementBitsReg( Component ):
  """
  Wrapper for the replacement bits register. We need it because we need more
  control on the bit level
  Works for 2 way asso
  """
  def construct( s, p ):

    s.wdata = InPort()
    s.wen   = InPort()
    s.waddr = InPort( p.BitsIdx )
    s.raddr = InPort( p.BitsIdx )
    s.rdata = OutPort()

    s.replacement_register = m = RegEnRst( p.BitsNlinesPerWay )
    m.en //= s.wen

    nblocks_per_way  = p.nblocks_per_way

    @update
    def update_register_bits():
      for i in range( nblocks_per_way ):
        if s.waddr == i:
          s.replacement_register.in_[i] @= s.wdata
        else:
          s.replacement_register.in_[i] @= s.replacement_register.out[i]

      s.rdata @= s.replacement_register.out[s.raddr]

  def line_trace( s ):
    msg = ""
    msg += f'bits[{s.replacement_register.out}]'
    return msg

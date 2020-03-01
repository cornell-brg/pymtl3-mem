"""
=========================================================================
 registers.py
=========================================================================
Our own version of registers that handles bitstructs better

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

from pymtl3                        import *

class PiplineRegEnRst( Component ):

  def construct( s, Type, reset_value ):
    s.out = OutPort( Type )
    s.in_ = InPort( Type )

    s.reset = InPort( int if Type is int else Bits1 )
    s.en    = InPort( int if Type is int else Bits1 )

    @s.update_ff
    def up_regenrst():
      if s.reset: s.out <<= reset_value
      elif s.en:  s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

"""
#=========================================================================
# StallEngine.py
#=========================================================================

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 29 March 2020
"""

from pymtl3 import *
from constants.constants import *
from pymtl3.stdlib.primitive  import Mux, RegEnRst, RegEn

class StallEngine( Component ):
  """
  Stalling Enginer for the outputs of the tag array.
  
  1. Ensures the read output from the tag array is saved in a register
  for when the cache stalls because we're only reading from the tag array once.
  
  2. Make sure that if the tag array is not read, we propagate 0's instead of
  the values from the read port of the tag array. This ensures no indeterminate
  values make their through the rest of the cache logic.

  """

  def construct( s, dtype ):

    s.in_ = InPort( dtype )
    s.en  = InPort()
    s.out = OutPort( dtype )

    s.stall_reg = m = RegEn( dtype )
    m.en  //= s.en
    m.in_ //= s.in_

    s.stall_mux = m = Mux( dtype, 2 )
    m.in_[0] //= s.in_
    m.in_[1] //= s.stall_reg.out
    m.out    //= s.out
    m.sel    //= lambda: ~s.en

  def line_trace( s ):
    return f'in:{s.in_} out:{s.out} en:{s.en} '

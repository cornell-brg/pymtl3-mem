"""
#=========================================================================
# StallEngine.py
#=========================================================================

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 29 March 2020
"""

from pymtl3 import *
from constants.constants import *
from pymtl3.stdlib.rtl.arithmetics  import Mux
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegEn

class StallEngine( Component ):

  def construct( s, dtype ):

    s.in_ = InPort( dtype )
    s.en  = InPort( Bits1 )
    s.out = OutPort( dtype )

    s.stall_reg = RegEn( dtype )(
      en  = s.en,
      in_ = s.in_
    )

    s.stall_mux_M2 = Mux( dtype, 2 )(
      in_ = {
        0: s.in_,
        1: s.stall_reg.out
      },
      out = s.out
    )
    s.stall_mux_M2.sel //= lambda: ~s.en

  def line_trace( s ):
    msg = ''
    msg += f'in:{s.in_} out:{s.out} en:{s.en} '
    return msg

'''
=========================================================================
counters.py
=========================================================================
RTL counters

Author: Moyang Wang
Date  : March 25, 2020
'''

from pymtl3 import *
from pymtl3.stdlib.rtl.registers import RegRst

class CounterEnRst( Component ):

  def construct( s, Type, reset_value=0 ):

    s.en         = InPort ( Bits1 )
    s.load       = InPort ( Bits1 )
    s.count_down = InPort ( Bits1 )
    s.load_value = InPort ( Type  )
    s.out        = OutPort( Type  )

    @s.update_ff
    def counter_ff_logic():
      if s.reset:
        s.out <<= Type( reset_value )
      elif s.en:
        if s.count_down:
          s.out <<= s.out - Type(1)
        else:
          s.out <<= s.out + Type(1)

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.out}]"


class CounterUpDown( Component ):
  def construct( s, Type, reset_value = 0 ):
    s.up_amt = InPort( Type )
    s.dw_amt = InPort( Type )
    s.ld_amt = InPort( Type )
    s.up_en = InPort( Bits1 )
    s.dw_en = InPort( Bits1 )
    s.ld_en = InPort( Bits1 )
    s.out   = OutPort( Type )

    s.counter = RegRst( Type, reset_value )
    s.out //= s.counter.out

    @s.update
    def counter_logic():
      s.counter.in_ = s.counter.out
      if s.ld_en:
        s.counter.in_ = s.ld_amt
      else:
        # state remains at 00 and 11
        if s.up_en & (~s.dw_en):
          s.counter.in_ = s.counter.out + s.up_amt
        elif ~s.up_en & s.dw_en:
          s.counter.in_ = s.counter.out - s.dw_amt
  
  def line_trace( s ):
    msg =''
    msg += f'[{s.counter.out}]'
    return msg

'''
=========================================================================
counters.py
=========================================================================
RTL counters

Author: Moyang Wang
Date  : March 25, 2020
'''

from pymtl3 import *

class CounterEnRst( Component ):

  def construct( s, Type, reset_value=0 ):

    s.reset      = InPort ( Bits1 )
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
        if s.load:
          s.out <<= s.load_value
        else:
          if s.count_down:
            s.out <<= s.out - Type(1)
          else:
            s.out <<= s.out + Type(1)

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.out}]"
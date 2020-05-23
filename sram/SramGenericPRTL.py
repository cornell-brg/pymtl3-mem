#=========================================================================
# Generic model of the SRAM
#=========================================================================
# This is meant to be instantiated within a carefully named outer module
# so the outer module corresponds to an SRAM generated with the
# CACTI-based memory compiler.

from pymtl3 import *

class SramGenericPRTL( Component ):

  def construct( s, num_bits = 32, num_words = 256 ):

    addr_width = clog2( num_words )      # address width
    dtype      = mk_bits( num_bits )

    # port names set to match the ARM memory compiler

    # clock (in PyMTL simulation it uses implict .clk port when
    # translated to Verilog, actual clock ports should be CE1

    s.CE1  = InPort ( Bits1 )               # clk
    s.WEB1 = InPort ( Bits1 )               # bar( write en )
    s.OEB1 = InPort ( Bits1 )               # bar( out en )
    s.CSB1 = InPort ( Bits1 )               # bar( whole SRAM en )
    s.A1   = InPort ( mk_bits(addr_width) ) # address
    s.I1   = InPort ( dtype )               # write data
    s.O1   = OutPort( dtype )               # read data
    s.WBM1 = InPort ( mk_bits( num_bits ) ) # bit-level write mask

    # memory array

    s.ram      = [ Wire( dtype ) for x in range( num_words ) ]
    s.ram_next = [ Wire( dtype ) for x in range( num_words ) ]

    # read path

    s.dout = Wire( dtype )
    s.dout_next = Wire( dtype )

    @update
    def read_logic():
      s.dout_next @= s.ram[ s.A1 ] if (~s.CSB1 & s.WEB1) else s.dout

    # write path
    @update
    def write_logic():
      for i in range( num_words ):
        s.ram_next[i] @= s.ram[i]
      for i in range( num_bits ):
        if ~s.CSB1 & ~s.WEB1 & s.WBM1[i]:
          s.ram_next[s.A1][i] @= s.I1[i]

    @update
    def comb_logic():
      s.O1 @= s.dout if ~s.OEB1 else 0

    @update_ff
    def update_sram():
      s.dout <<= s.dout_next
      for i in range( num_words ):
        s.ram[i] <<= s.ram_next[i]

  def line_trace( s ):
    return f"(WE={~s.WEB1} OE={~s.OEB1} A1={s.A1} I1A={s.I1} O1={s.O1} s.WBM1={s.WBM1})"

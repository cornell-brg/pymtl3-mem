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
    nbytes     = int( num_bits + 7 ) // 8 # $ceil(num_bits/8)

    dtype = mk_bits( num_bits )

    # port names set to match the ARM memory compiler

    # clock (in PyMTL simulation it uses implict .clk port when
    # translated to Verilog, actual clock ports should be CE1

    s.CE1  = InPort ( Bits1 )          # clk
    s.WEB1 = InPort ( Bits1 )          # bar( write en )
    s.OEB1 = InPort ( Bits1 )          # bar( out en )
    s.CSB1 = InPort ( Bits1 )          # bar( whole SRAM en )
    s.A1   = InPort ( mk_bits(addr_width) ) # address
    s.I1   = InPort ( dtype )   # write data
    s.O1   = OutPort( dtype )   # read data
    s.WBM1 = InPort ( mk_bits(nbytes) )     # byte write en

    # memory array

    s.ram      = [ Wire( dtype ) for x in range( num_words ) ]
    s.ram_next = [ Wire( dtype ) for x in range( num_words ) ]

    # read path

    s.dout = Wire( dtype )
    s.dout_next = Wire( dtype )
    

    @s.update
    def read_logic():
      if ( not s.CSB1 ) and s.WEB1:
        s.dout_next = s.ram[ s.A1 ]
      else:
        s.dout_next = dtype(0)

    # write path

    @s.update
    def write_logic():
      for i in range( nbytes ):
        if ~s.CSB1 and ~s.WEB1 and s.WBM1[i]:
          s.ram_next[s.A1][ i*8 : i*8+8 ] = dtype(s.I1)[ i*8 : i*8+8 ]

    @s.update
    def comb_logic():
      if not s.OEB1:
        s.O1 = s.dout
      else:
        s.O1 = dtype(0)
    
    @s.update_on_edge
    def update_sram():
      s.dout = dtype( s.dout_next )
      for i in range( num_words ):
        s.ram[i] = dtype( s.ram_next[i] )

    # s.add_constraints( U(read_logic)<U(write_logic)<U(update_sram)<U(comb_logic) )

  def line_trace( s ):
    # print ([int(x) for x in s.ram], [int(x) for x in s.ram_next])
    return "(WE={} OE={} A1={} I1A={} O1={} s.WBM1={})".format(~s.WEB1, ~s.OEB1, s.A1, s.I1, s.O1, s.WBM1)

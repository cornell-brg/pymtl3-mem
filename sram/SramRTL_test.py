#=======================================================================
# SramRTL_test.py
#=======================================================================
# Unit Tests for SRAM RTL model

import pytest
import random

from pymtl        import *
from sram.SramPRTL import SramPRTL as SramRTL

#-------------------------------------------------------------------------
# run_test_vector_sim
#-------------------------------------------------------------------------

def run_test_vector_sim( model, test_vectors, dump_vcd=None, test_verilog=False ):

  # First row in test vectors contains port names

  if isinstance(test_vectors[0],str):
    port_names = test_vectors[0].split()
  else:
    port_names = test_vectors[0]

  # Remaining rows contain the actual test vectors

  test_vectors = test_vectors[1:]

  # Setup the model

  # Create a simulator

  sim = model()

  sim.apply( SimpleSim )

  # Reset model

  sim.reset()
  print ""

  # Run the simulation

  row_num = 0
  for row in test_vectors:
    print
    print "start a new vector:"
    row_num += 1

    # Apply test inputs

    for port_name, in_value in zip( port_names, row ):
      if port_name[-1] != "*":

        # Special case for lists of ports
        if '[' in port_name:
          m = re.match( r'(\w+)\[(\d+)\]', port_name )
          if not m:
            raise Exception("Could not parse port name: {}".format(port_name))
          getattr( model, m.group(1) )[int(m.group(2))] = in_value
          #getattr( model, m.group(1) )[int(m.group(2))].value = in_value
        else:
          getattr( model, port_name ).value = in_value

    # Evaluate combinational concurrent blocks

    sim.tick()

    # Display line trace output

    #print sim.line_trace()

    # Check test outputs

    for port_name, ref_value in zip( port_names, row ):
      if port_name[-1] == "*":

        # Special case for lists of ports
        if '[' in port_name:
          m = re.match( r'(\w+)\[(\d+)\]', port_name[0:-1] )
          if not m:
            raise Exception("Could not parse port name: {}".format(port_name))
          out_value = getattr( model, m.group(1) )[int(m.group(2))]
        else:
          out_value = getattr( model, port_name[0:-1] )

        if ( ref_value != '?' ) and ( out_value != ref_value ):

          error_msg = """
 run_test_vector_sim received an incorrect value!
  - row number     : {row_number}
  - port name      : {port_name}
  - expected value : {expected_msg}
  - actual value   : {actual_msg}
""".format(
            row_number   = row_num,
            port_name    = port_name,
            expected_msg = ref_value,
            actual_msg   = out_value
          )
          print error_msg
          assert False

    # Tick the simulation

    sim.tick()

  # Extra ticks to make VCD easier to read

  sim.tick()
  sim.tick()
  sim.tick()

#-----------------------------------------------------------------------
# Directed test for 32x256 SRAM
#-----------------------------------------------------------------------

def test_direct_32x256( dump_vcd, test_verilog ):
  test_vectors = [ header_str,
    # val,  type,  wben,    idx,  wdata,      rdata
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 1,  0b1111,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x00000000 ],
    [    1, 1,  0b0001,     0, 0xdeadbeef, 0x00000000 ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x000000ef ],
    [    1, 1,  0b0110,     0, 0xabcdefab, 0x000000ef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x00cdefef ],
    [    1, 1,  0b1011,     0, 0xff000000, 0x00cdefef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xffcd0000 ],
    [    1, 1,  0b1111,     0, 0xdeadbeef, 0xffcd0000 ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xdeadbeef ],
    [    1, 1,  0b1111,     0, 0xffffffff, 0xdeadbeef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xffffffff ],
    [    1, 0,  0b0000,  0xfe, 0x00000000, 0xffffffff ],
    [    1, 1,  0b1111,  0xfe, 0xdeadbeef, '?'        ],
    [    1, 0,  0b1111,  0xfe, 0xbbbbcccc, '?'        ],
    [    1, 0,  0b0000,  0xfe, 0x00000000, 0xdeadbeef ],
  ]
  run_test_vector_sim( SramRTL(32, 256), test_vectors, dump_vcd, test_verilog )

#-----------------------------------------------------------------------
# Directed test for 128x256 SRAM
#-----------------------------------------------------------------------

def test_direct_128x256( dump_vcd, test_verilog ):
  test_vectors = [ header_str,
    # val,  type,  wben,    idx,  wdata,      rdata
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 1,  0b1111,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x00000000 ],
    [    1, 1,  0b0001,     0, 0xdeadbeef, 0x00000000 ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x000000ef ],
    [    1, 1,  0b0110,     0, 0xabcdefab, 0x000000ef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x00cdefef ],
    [    1, 1,  0b1011,     0, 0xff000000, 0x00cdefef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xffcd0000 ],
    [    1, 1,  0b1111,     0, 0xdeadbeef, 0xffcd0000 ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xdeadbeef ],
    [    1, 1,  0b1111,     0, 0xffffffff, 0xdeadbeef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xffffffff ],
    [    1, 0,  0b0000,  0xff, 0x00000000, 0xffffffff ],
    [    1, 1,  0b1111,  0xff, 0xdeadbeef, '?'        ],
    [    1, 0,  0b1111,  0xff, 0xbbbbcccc, '?'        ],
    [    1, 0,  0b0000,  0xff, 0x00000000, 0xdeadbeef ],
  ]
  run_test_vector_sim( SramRTL(128, 256), test_vectors, dump_vcd, test_verilog )


#-----------------------------------------------------------------------
# Directed test for 128x256 SRAM
#-----------------------------------------------------------------------

def test_direct_128x512( dump_vcd, test_verilog ):
  test_vectors = [ header_str,
    # val,  type,  wben,    idx,  wdata,      rdata
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 1,  0b1111,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x00000000 ],
    [    1, 1,  0b0001,     0, 0xdeadbeef, 0x00000000 ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x000000ef ],
    [    1, 1,  0b0110,     0, 0xabcdefab, 0x000000ef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0x00cdefef ],
    [    1, 1,  0b1011,     0, 0xff000000, 0x00cdefef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xffcd0000 ],
    [    1, 1,  0b1111,     0, 0xdeadbeef, 0xffcd0000 ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xdeadbeef ],
    [    1, 1,  0b1111,     0, 0xffffffff, 0xdeadbeef ],
    [    1, 0,  0b0000,     0, 0x00000000, '?'        ],
    [    1, 0,  0b0000,     0, 0x00000000, 0xffffffff ],
    [    1, 0,  0b0000, 0x1ff, 0x00000000, 0xffffffff ],
    [    1, 1,  0b1111, 0x1ff, 0xdeadbeef, '?'        ],
    [    1, 0,  0b1111, 0x1ff, 0xbbbbcccc, '?'        ],
    [    1, 0,  0b0000, 0x1ff, 0x00000000, 0xdeadbeef ],
  ]
  run_test_vector_sim( SramRTL(128, 512), test_vectors, dump_vcd, test_verilog )

header_str = \
  ( "port0_val", "port0_type", "port0_wben",  "port0_idx",
    "port0_wdata", "port0_rdata*" )

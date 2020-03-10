#=======================================================================
# SramRTL_test.py
#=======================================================================
# Unit Tests for SRAM RTL model

import pytest
import random

from pymtl3        import *
from sram.SramPRTL import SramPRTL as SramRTL
from pymtl3.stdlib.test import run_test_vector_sim

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

"""
=========================================================================
 OtherCiferTests.py
=========================================================================
"""

import pytest
from test.sim_utils import SingleCacheTestParams

inv_flush_mem = [
  0x00000000, 1,
  0x00000004, 2,
  0x00000008, 3,
  0x0000000c, 4,
  0x00000010, 0x11,
  0x00000014, 0x12,
  0x00000018, 0x13,
  0x0000001c, 0x14,
  0x00000020, 0x21,
  0x00000024, 0x22,
  0x00000028, 0x23,
  0x0000002c, 0x24,
  0x00000030, 0x31,
  0x00000034, 0x32,
  0x00000038, 0x33,
  0x0000003c, 0x34,
  0x00020000, 5,
  0x00020004, 6,
  0x00020008, 7,
  0x0002000c, 8,
  0x00020010, 9,
  0x00020014, 0xa,
  0x00020018, 0xb,
  0x0002001c, 0xc,
  0x00030000, 0xd,
  0x00030004, 0xe,
  0x00030008, 0xf,
  0x0003000c, 0x10,
  0x00030010, 0xaaa,
  0x00030014, 0xbbb,
  0x00030018, 0xdeadbeef,
  0x0003001c, 0xffc0ffee,
  0x0000005c, 9,
  0x00000060, 0xa,
]

#-------------------------------------------------------------------------
# Test cases
#-------------------------------------------------------------------------

def len3_short():
  msg =  [
    # type   opq addr        len data               type   opq test len data
    ( 'rd',  1,  0x00020010, 0,  0          ),    ( 'rd',  1,  0,   0,  0x09       ),
    ( 'rd',  2,  0x00020014, 0,  0          ),    ( 'rd',  2,  1,   0,  0x0a       ),
    ( 'wr',  3,  0x00020010, 0,  0xdead     ),    ( 'wr',  3,  1,   0,  0          ),
    ( 'rd',  4,  0x00020010, 0,  0          ),    ( 'rd',  4,  1,   0,  0xdead     ),
    ( 'rd',  5,  0x00020014, 0,  0          ),    ( 'rd',  5,  1,   0,  0x0a       ),
    ( 'wr',  6,  0x00020010, 3,  0xbeef     ),    ( 'wr',  6,  1,   3,  0          ),
    ( 'rd',  7,  0x00020010, 0,  0          ),    ( 'rd',  7,  1,   0,  0xbeef     ),
    ( 'rd',  8,  0x00020014, 0,  0          ),    ( 'rd',  8,  1,   0,  0          ),
    ( 'rd',  9,  0x00030018, 0,  0          ),    ( 'rd',  9,  0,   0,  0xdeadbeef ),
    ( 'rd', 10,  0x0003001c, 0,  0          ),    ( 'rd', 10,  1,   0,  0xffc0ffee ),
    ( 'wr', 11,  0x00030018, 0,  0xfff0fff0 ),    ( 'wr', 11,  1,   0,  0          ),
    ( 'rd', 12,  0x00030018, 0,  0          ),    ( 'rd', 12,  1,   0,  0xfff0fff0 ),
    ( 'rd', 13,  0x0003001c, 0,  0          ),    ( 'rd', 13,  1,   0,  0xffc0ffee ),
    ( 'wr', 14,  0x00030018, 3,  0xdeaddead ),    ( 'wr', 14,  1,   3,  0          ),
    ( 'rd', 15,  0x00030018, 0,  0          ),    ( 'rd', 15,  1,   0,  0xdeaddead ),
    ( 'rd', 16,  0x0003001c, 0,  0          ),    ( 'rd', 16,  1,   0,  0          ),
  ]
  return SingleCacheTestParams( msg, inv_flush_mem, associativity=2, bitwidth_mem_data=128,
                                bitwidth_cache_data=32, cache_size=4096 )

#-------------------------------------------------------------------------
# Test driver
#-------------------------------------------------------------------------

class OtherCiferTests:
  @pytest.mark.parametrize(
    " name,    test,                stall_prob,latency,src_delay,sink_delay", [
    ("256B-0", len3_short,          0,         1,      0,        0   ),
  ])
  def test_other_cifer( s, name, test, stall_prob, latency, src_delay, sink_delay,
                        cmdline_opts, line_trace ):
    p = test()
    s.run_test( p.msg, p.mem, p.CacheReqType, p.CacheRespType, p.MemReqType, p.MemRespType,
                p.associativity, p.size, stall_prob, latency, src_delay, sink_delay,
                cmdline_opts, line_trace )

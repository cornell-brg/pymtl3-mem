"""
#=========================================================================
# constants.py
#=========================================================================
Important constants for the cache

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from pymtl3 import *
from pymtl3.stdlib.ifcs.MemMsg       import MemMsgType

# Constants
wr = y             = b1(1)
rd = n = x         = b1(0)

STATE_GO           = b3(0)
STATE_REFILL       = b3(1)
STATE_EVICT        = b3(2)
STATE_REFILL_WRITE = b3(3)

data_array_double_mask = 0xff
data_array_word_mask   = 0xf
data_array_2byte_mask  = 0x3
data_array_byte_mask   = 0x1

READ  = b4(MemMsgType.READ)
WRITE = b4(MemMsgType.WRITE)
INIT  = b4(MemMsgType.WRITE_INIT)

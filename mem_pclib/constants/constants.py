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

data_array_double_mask = 0xff
data_array_word_mask   = 0xf
data_array_2byte_mask  = 0x3
data_array_byte_mask   = 0x1

READ  = b4(MemMsgType.READ)
WRITE = b4(MemMsgType.WRITE)
INIT  = b4(MemMsgType.WRITE_INIT)
AMO_ADD    = b4(MemMsgType.AMO_ADD)
AMO_AND    = 4
AMO_OR     = 5
AMO_SWAP   = 6
AMO_MIN    = 7
AMO_MINU   = 8
AMO_MAX    = 9
AMO_MAXU   = 10
AMO_XOR    = 11 


#=========================================================================
#  Ctrl states
#=========================================================================

IDLE   = b1(0)
REPLAY = b1(1)


# INVALID         = 0
# VALID           = 1
# REFILL          = 2 # valid and refilling
# WRITE_REFILL    = 3
# WRITE_HIT_CLEAN = 4
# AMO             = 5

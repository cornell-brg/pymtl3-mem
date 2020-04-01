"""
#=========================================================================
# constants.py
#=========================================================================
BlockingCache-specific constants

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from pymtl3 import *

#-------------------------------------------------------------------------
# Cacheline states
#-------------------------------------------------------------------------

CACHE_LINE_STATE_INVALID = b2(0b00)
CACHE_LINE_STATE_PARTIAL = b2(0b01)
CACHE_LINE_STATE_VALID   = b2(0b11)

#-------------------------------------------------------------------------
# Write masks
#-------------------------------------------------------------------------

data_array_double_mask = 0xff
data_array_word_mask   = 0xf
data_array_2byte_mask  = 0x3
data_array_byte_mask   = 0x1

#-------------------------------------------------------------------------
# UpdateTagArrayUnit
#-------------------------------------------------------------------------
# Command for UpdateTagArrayUnit

UpdateTagArrayUnit_CMD_NONE      = b3(0) # No action
UpdateTagArrayUnit_CMD_CLEAR     = b3(1) # Clear the entry
UpdateTagArrayUnit_CMD_WR_HIT    = b3(2) # Hit a clean word, mark it as dirty
UpdateTagArrayUnit_CMD_WR_REFILL = b3(3) # Refill on a write
UpdateTagArrayUnit_CMD_RD_REFILL = b3(4) # Refill on a read
UpdateTagArrayUnit_CMD_INV       = b3(5) # Invalidate this cache line
UpdateTagArrayUnit_CMD_FLUSH     = b3(6) # Flush this cache line


"""
#=========================================================================
# cache_constants.py
#=========================================================================
BlockingCache-specific constants

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 10 February 2020
"""

from pymtl3 import *
from pymtl3_mem.mem_ifcs.MemMsg import MemMsgType

#-------------------------------------------------------------------------
# Cacheline states
#-------------------------------------------------------------------------

CACHE_LINE_STATE_INVALID = b1(0)
CACHE_LINE_STATE_VALID   = b1(1)

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

#-------------------------------------------------------------------------
# WriteBitEnGen
#-------------------------------------------------------------------------
# Command for write bit enable generator
WriteBitEnGen_CMD_NONE  = b2(0) # All bits zero - no action
WriteBitEnGen_CMD_REQ   = b2(1) # Gen bits based on current request
WriteBitEnGen_CMD_DIRTY = b2(2) # Gen bits based on inverted dirty bits

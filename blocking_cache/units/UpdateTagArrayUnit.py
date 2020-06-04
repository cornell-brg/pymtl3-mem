"""
=========================================================================
UpdateTagArrayUnit.py
=========================================================================
Generate new tag array entry based on previous content.

Author: Moyang Wang (mw828)
Date:   17 March 2020
"""

from pymtl3 import *

from ..cache_constants import *

class UpdateTagArrayUnit( Component ):
  """
  Selects the tag array write data depending on command 
  """
  def construct( s, p ):
    s.way         = InPort (p.bitwidth_clog_asso) # Select the way to update
    s.offset      = InPort (p.bitwidth_offset)
    s.old_entries = [ InPort(p.StructTagArray) for _ in range(p.associativity) ]
    s.cmd         = InPort (3)
    s.refill_dty  = InPort (p.bitwidth_dirty)
    s.out         = OutPort(p.StructTagArray)

    @update
    def new_tag_array_entry_logic():
      s.out.tag @= s.old_entries[s.way].tag
      s.out.val @= s.old_entries[s.way].val
      s.out.dty @= s.old_entries[s.way].dty
      if s.cmd == UpdateTagArrayUnit_CMD_WR_REFILL:
        # Refill on a write, mark the word being written as dirty, the
        # rest is clean
        s.out.val @= CACHE_LINE_STATE_VALID
        s.out.dty @= 0 | s.refill_dty
        s.out.dty[ s.offset[2 : p.bitwidth_offset] ] @= 1
      elif s.cmd == UpdateTagArrayUnit_CMD_RD_REFILL:
        # Refill for a read, simply mark valid bit and clear the dirty
        # bits
        s.out.val @= CACHE_LINE_STATE_VALID
        s.out.dty @= 0 | s.refill_dty
      elif s.cmd == UpdateTagArrayUnit_CMD_WR_HIT:
        # Hit a clean word, mark the word as dirty
        s.out.dty[ s.offset[2 : p.bitwidth_offset] ] @= 1
      elif s.cmd == UpdateTagArrayUnit_CMD_CLEAR:
        # Clear the entire entry
        s.out.tag @= 0
        s.out.val @= CACHE_LINE_STATE_INVALID
        s.out.dty @= 0
      elif s.cmd == UpdateTagArrayUnit_CMD_INV:
        # For cache invalidation, leave the dirty bits as is, clear the
        # valid bit
        s.out.val @= CACHE_LINE_STATE_INVALID

  def line_trace( s ):
    msg = ""
    msg += f"new:{s.out} old:{s.old_entries} cmd:{s.cmd}"
    return msg

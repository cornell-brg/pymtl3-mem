"""
=========================================================================
 MSHR.py
=========================================================================
Parameterizable MSHR

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 12 February 2020
"""

from pymtl3                         import *
from pymtl3.stdlib.ifcs.SendRecvIfc import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.rtl.registers    import RegEnRst, RegRst, Reg, RegEn
from pymtl3.stdlib.rtl.arithmetics  import Mux

from constants.constants import *

from .registers import MSHRReg

class MSHR (Component):

  def construct( s , p, entries ):

    BitsEntries   = mk_bits( clog2( entries + 1 ) )

    s.alloc_en    = InPort (Bits1)
    s.alloc_in    = InPort (p.MSHRMsg)
    s.full        = OutPort(Bits1)
    s.alloc_id    = OutPort(p.BitsOpaque)

    s.dealloc_id  = InPort (p.BitsOpaque)
    s.dealloc_en  = InPort (Bits1)
    s.dealloc_out = OutPort(p.MSHRMsg)
    s.empty       = OutPort(Bits1) # high when no more secondary misses?

    # Number of free MSHR Entries
    s.num_entries_in  = Wire(BitsEntries)
    s.num_entries_reg = RegRst(BitsEntries)(
      in_ = s.num_entries_in,
    )

    @s.update
    def entry_logic():
      s.num_entries_in = s.num_entries_reg.out
      if s.alloc_en:    # No parallel alloc/dealloc
        s.num_entries_in = s.num_entries_reg.out + BitsEntries(1)
      elif s.dealloc_en:
        s.num_entries_in = s.num_entries_reg.out - BitsEntries(1)

    @s.update
    def full_logic():
      s.full = n
      s.empty = n
      if s.num_entries_reg.out == BitsEntries(entries) or \
        (s.num_entries_reg.out == BitsEntries(entries - 1) and s.alloc_en):
        # Considered full if num entries is equal to max entries or if we
        # have one less and are allocating an entry
        s.full = y
      if s.num_entries_reg.out == BitsEntries(0):
        s.empty = y

    if entries == BitsEntries(1):
      s.storage_regs = MSHRReg( p )(
        in_ = s.alloc_in,
        out = s.dealloc_out,
        en  = s.alloc_en
      )
      s.alloc_id //= s.alloc_in.opaque

  def line_trace(s):
    msg = ""
    msg += f" c:{s.num_entries_reg.out}"
    return msg

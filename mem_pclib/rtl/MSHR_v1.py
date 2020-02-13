"""
#=========================================================================
# MSHR.py
#=========================================================================


Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 12 February 2020
"""

from pymtl3 import *
from mem_pclib.rtl.utils import ECompEn
from pymtl3.stdlib.ifcs.SendRecvIfc       import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.rtl.registers import RegEnRst, RegRst, Reg, RegEn
from pymtl3.stdlib.rtl.arithmetics  import Mux
from mem_pclib.constants.constants   import *

class MSHR (Component):

  def construct( s, param, entries ):

    BitsEntries   = clog2( entries + 1 )  

    s.alloc_en    = InPort(Bits1)
    s.alloc_in    = InPort(param.MSHRMsg)
    s.full        = OutPort(Bits1)
    s.alloc_id    = OutPort(param.BitsOpaque)

    s.dealloc_id  = InPort(param.BitsOpaque)
    s.dealloc_en  = InPort(Bits1)
    s.dealloc_out = OutPort(param.MSHRMsg)
    s.empty       = OutPort(Bit1) # high when no more secondary misses?

    # Count of free MSHR Entries
    s.num_entries_in = Wire(BitsEntries)
    s.num_entries_out = Wire(BitsEntries)
    s.num_entries_reg = RegRst(BitsEntries)(
      in_ = s.num_entries_in,
      out = s.num_entries_out
    )
    @s.update
    def entry_logic():
      s.num_entries_in = s.num_entries_out
      if s.alloc_en:    # No parallel alloc/dealloc
        s.num_entries_in = s.num_entries_out + BitsEntries(1)
      elif s.dealloc_en:
        s.num_entries_in = s.num_entries_out - BitsEntries(1)

    @s.update
    def full_logic():
      s.full = n
      s.empty = n
      if s.num_entries_out == entries:
        s.full = y
      if s.num_entries_out == 0:
        s.empty = y

    if entries == 1:
      s.MSHR = RegEnRst(param.MSHRMsg)(
        in_ = s.alloc_in,
        out = s.dealloc_out,
        en  = s.alloc_en
      )
      s.alloc_id //= s.alloc_in.opaque


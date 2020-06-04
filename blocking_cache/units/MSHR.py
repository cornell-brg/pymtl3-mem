  
"""
=========================================================================
 MSHR.py
=========================================================================
Parameterizable MSHR
Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 12 February 2020
"""

from pymtl3                  import *
from pymtl3.stdlib.ifcs      import RecvIfcRTL, SendIfcRTL
from pymtl3.stdlib.basic_rtl import RegEnRst, RegRst, Reg, RegEn, Mux
from constants.constants import *

class MSHR(Component):
  """
  Miss Status Hit Register - keeps track of outstanding misses
  Blocks if all entries all filled

  For blocking cache, it is 1 entry
  """
  def construct( s, p, entries ):
    s.alloc_en    = InPort ()
    s.alloc_in    = InPort (p.MSHRMsg)
    s.full        = OutPort()
    s.alloc_id    = OutPort(p.bitwidth_opaque)

    s.dealloc_id  = InPort (p.bitwidth_opaque)
    s.dealloc_en  = InPort ()
    s.dealloc_out = OutPort(p.MSHRMsg)
    s.empty       = OutPort() # high when no more secondary misses?

    # Number of free MSHR Entries
    bitwidth_entries = clog2(entries + 1)
    s.num_entries_in  = Wire(bitwidth_entries)
    s.num_entries_reg = m = RegRst(bitwidth_entries)
    m.in_ //= s.num_entries_in

    @update
    def entry_logic():
      if s.alloc_en:    # No parallel alloc/dealloc
        s.num_entries_in @= s.num_entries_reg.out + 1
      elif s.dealloc_en:
        s.num_entries_in @= s.num_entries_reg.out - 1
      else:
        s.num_entries_in @= s.num_entries_reg.out

    @update
    def full_logic():
      # Considered full if num entries is equal to max entries or if we
      # have one less and are allocating an entry
      s.full  @= (s.num_entries_reg.out == entries) | ((s.num_entries_reg.out == entries-1) & s.alloc_en)
      s.empty @= (s.num_entries_reg.out == 0)

    if entries == 1:
      s.storage_regs = m = RegEnRst( p.MSHRMsg, p.MSHRMsg() )
      m.in_ //= s.alloc_in
      m.out //= s.dealloc_out
      m.en  //= s.alloc_en

      s.alloc_id //= s.alloc_in.opaque

  def line_trace(s):
    msg = ""
    msg += f" c:{s.num_entries_reg.out}"
    return msg

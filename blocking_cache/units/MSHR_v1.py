  
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

  def construct( s, p, entries ):

    BitsEntries   = mk_bits( clog2( entries + 1 ) )

    s.alloc_en    = InPort ()
    s.alloc_in    = InPort (p.MSHRMsg)
    s.full        = OutPort()
    s.alloc_id    = OutPort(p.BitsOpaque)

    s.dealloc_id  = InPort (p.BitsOpaque)
    s.dealloc_en  = InPort ()
    s.dealloc_out = OutPort(p.MSHRMsg)
    s.empty       = OutPort() # high when no more secondary misses?

    # Number of free MSHR Entries
    s.num_entries_in  = Wire(BitsEntries)
    s.num_entries_reg = m = RegRst(BitsEntries)
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
      s.storage_regs = m = MSHRReg( p )
      m.in_ //= s.alloc_in
      m.out //= s.dealloc_out
      m.en  //= s.alloc_en

      s.alloc_id //= s.alloc_in.opaque

  def line_trace(s):
    msg = ""
    msg += f" c:{s.num_entries_reg.out}"
    return msg

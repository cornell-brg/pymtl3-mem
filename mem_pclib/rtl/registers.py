"""
=========================================================================
 registers.py
=========================================================================
Our own version of registers that handles bitstructs better

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

from pymtl3                        import *

class DpathPipelineRegM0 ( Component ):
  def construct( s, p ):
    s.out = OutPort( p.MemRespType )
    s.in_ = InPort( p.MemRespType )

    s.reset = InPort( Bits1 )
    s.en    = InPort( Bits1 )

    BitsLen =  mk_bits(clog2(p.bitwidth_cacheline>>3))
    s.reset_value = Wire(p.MemRespType)
    s.reset_value //= p.MemRespType(
      p.BitsType(0), p.BitsOpaque(0), b2(0), BitsLen(0),
      p.BitsCacheline(0)
    )
    @s.update_ff
    def up_regenrst():
      if s.reset: s.out <<= s.reset_value
      elif s.en:  s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

class DpathPipelineReg( Component ):

  def construct( s, p ):
    s.out = OutPort( p.PipelineMsg )
    s.in_ = InPort( p.PipelineMsg )

    s.reset = InPort( Bits1 )
    s.en    = InPort( Bits1 )

    s.reset_value = Wire(p.PipelineMsg)
    s.reset_value //= p.PipelineMsg(
      p.BitsType(0), p.BitsOpaque(0), p.StructAddr(p.BitsTag(0),p.BitsIdx(0),\
        p.BitsOffset(0)), p.BitsLen(0), p.BitsCacheline(0)
    )
    @s.update_ff
    def up_regenrst():
      if s.reset: s.out <<= s.reset_value
      elif s.en:  s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

class CtrlPipelineReg( Component ):

  def construct( s, p ):
    s.out = OutPort( p.CtrlMsg )
    s.in_ = InPort( p.CtrlMsg )

    s.reset = InPort( Bits1 )
    s.en    = InPort( Bits1 )

    s.reset_value = Wire(p.CtrlMsg)
    s.reset_value //= p.CtrlMsg(b1(0),b1(0),b1(0),b1(0)) 
    @s.update_ff
    def up_regenrst():
      if s.reset: s.out <<= s.reset_value
      elif s.en:  s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

class MSHRReg( Component ):

  def construct( s, p ):
    s.out = OutPort( p.MSHRMsg )
    s.in_ = InPort( p.MSHRMsg )

    s.reset = InPort( Bits1 )
    s.en    = InPort( Bits1 )

    s.reset_value = Wire(p.MSHRMsg)
    s.reset_value //= p.MSHRMsg(
      p.BitsType(0), p.BitsOpaque(0), p.BitsAddr(0), p.BitsLen(0), p.BitsCacheline(0), p.BitsAssoclog2(0)
    )
    @s.update_ff
    def up_regenrst():
      if s.reset: s.out <<= s.reset_value 
      elif s.en:  s.out <<= s.in_

  def line_trace( s ):
    return f"[{'en' if s.en else '  '}|{s.in_} > {s.out}]"

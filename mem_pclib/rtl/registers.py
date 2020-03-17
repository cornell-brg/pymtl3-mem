"""
=========================================================================
 registers.py
=========================================================================
Our own version of registers that handles bitstructs better

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 1 March 2020
"""

from pymtl3                      import *
from pymtl3.stdlib.rtl.registers import RegEnRst, RegEn, RegRst

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


class ValReg( Component ):  
  """
  Wrapper for the valid bits register. We need it because we need more control
  on the bit level
  """
  def construct( s, p ):
    s.out   = OutPort( Bits1 )
    s.in_   = InPort( Bits1 )
    s.en    = InPort( Bits1 )
    s.wen   = InPort( Bits1 )
    s.waddr = InPort( p.BitsIdx )
    s.raddr = InPort( p.BitsIdx )

    s.storage_reg = RegEnRst( p.BitsNlinesPerWay, 0 )
    
    s.en_req = RegRst( Bits1 )(
      in_ = s.en,
    )    
    
    BitsIdx = p.BitsIdx
    nblocks_per_way  = p.nblocks_per_way
    @s.update
    def reg_logic():
      for i in range( nblocks_per_way ):
        if s.waddr == BitsIdx(i):
          s.storage_reg.in_[i] = s.in_
        else:
          s.storage_reg.in_[i] = s.storage_reg.out[i]
      s.storage_reg.en  = s.en & s.wen 
      if s.en_req.out:
        s.out = s.storage_reg.out[s.raddr]
      else:
        s.out = b1(0)

  def line_trace( s ):
    msg = ""
    msg += f"waddr:{s.waddr} raddr:{s.raddr} out:{s.out} en:{s.en} wen:{s.wen} "
    # msg += f"reg:{s.reg.out} "
    return msg

class ReplacementBitsReg( Component ):
  """
  Wrapper for the replacement bits register. We need it because we need more 
  control on the bit level
  Works for 2 way asso
  """
  def construct( s, p ):
    s.wdata = InPort( Bits1 )
    s.wen   = InPort( Bits1 )
    s.waddr = InPort( p.BitsIdx )
    s.raddr = InPort( p.BitsIdx )
    s.rdata = OutPort( Bits1 )

    s.replacement_register = RegEnRst( p.BitsNlinesPerWay )(
      en  = s.wen,
    )
    nblocks_per_way  = p.nblocks_per_way
    BitsIdx = p.BitsIdx
    @s.update
    def update_register_bits():
      for i in range( nblocks_per_way ):
        if s.waddr == BitsIdx(i):
          s.replacement_register.in_[i] = s.wdata
        else:
          s.replacement_register.in_[i] = s.replacement_register.out[i]

      s.rdata = s.replacement_register.out[s.raddr]

"""
=========================================================================
 ctrlStructs.py
=========================================================================
Bitstructs used within the cache control module

Author : Xiaoyu Yan (xy97), Eric Tang (et396)
Date   : 2 February 2020
"""

from pymtl3 import *

def mk_ctrl_pipeline_struct(  ):
  cls_name    = f"CtrlMsg"

  def req_to_str( self ):
    return "{}:{}:{}:{}".format(
      Bits1( self.val ),
      BitsAddr( self.is_refill ),
      BitsLen( self.is_write_hit_clean ),
      BitsData( self.is_write_refill ),
    )

  req_cls = mk_bitstruct( cls_name, 
    {
      'val'               : Bits1,
      'is_refill'         : Bits1,
      'is_write_hit_clean': Bits1,
      'is_write_refill'   : Bits1,
    },
    namespace = {'__str__' : req_to_str}
  )

  return req_cls
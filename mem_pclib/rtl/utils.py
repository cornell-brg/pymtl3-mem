"""
#=========================================================================
# utils.py
#=========================================================================
Implement some general stdlib models so we can keep everything structural

Author : Xiaoyu Yan, Eric Tang
Date   : 11/04/19
"""


from pymtl3 import *

class EComp ( Component ):

  def construct( s, Type ):
    s.in0 = InPort( Type )
    s.in1 = InPort( Type )
    s.out = OutPort( bool if Type is int else Bits1 )

    @s.update
    def up_ecomp():
      s.out = Bits1(s.in0 == s.in1)

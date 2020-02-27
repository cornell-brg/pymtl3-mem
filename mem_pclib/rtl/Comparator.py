'''
=========================================================================
Comparator.py
=========================================================================
Determine whether a hit occurred and which way if associativity > 1


Author: Eric Tang (et396), Xiaoyu Yan (xy97) 
Date:   27 February 2020
'''

from mem_pclib.constants.constants   import *
from pymtl3 import *

class Comparator( Component ):

  def construct(s, p):

    s.addr_tag       = InPort (p.BitsTag)
    s.tag_array_val  = InPort (p.BitsAssoc)
    s.tag_array_data = [ InPort(p.BitsTagArray) for _ in range(p.associativity) ]
    
    s.hit            = OutPort(Bits2)
    s.hit_way        = OutPort(p.BitsAssoclog2)

    @s.update
    def Comparator():
      s.hit     = n
      s.hit_way = p.BitsAssoclog2(0)
      for i in range( p.associativity ):
        if ( s.tag_array_val ):
          if s.tag_array_data[i][0:p.bitwidth_tag] == s.addr_tag:
            s.hit = y
            s.hit_way = p.BitsAssoclog2(i) 
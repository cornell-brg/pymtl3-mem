'''
=========================================================================
Comparator.py
=========================================================================
Determine whether a hit occurred by comparing the tag from the tag array
with the tag from the address if the entry in the tag array is valid

Author: Eric Tang (et396), Xiaoyu Yan (xy97) 
Date:   27 February 2020
'''

from mem_pclib.constants.constants   import *
from pymtl3 import *

class Comparator( Component ):

  def construct(s, p):

    s.addr_tag  = InPort(p.BitsTag)
    s.tag_array = [ InPort(p.StructTagArray) for _ in range(p.associativity) ]
    s.hit       = OutPort(Bits1)
    s.hit_way   = OutPort(p.BitsAssoclog2)

    BitsAssoclog2 = p.BitsAssoclog2
    associativity = p.associativity
    @s.update
    def comparing_logic():
      s.hit     = n
      s.hit_way = BitsAssoclog2(0)
      for i in range( associativity ):
        if ( s.tag_array[i].val ):
          if s.tag_array[i].tag == s.addr_tag:
            s.hit = y
            s.hit_way = BitsAssoclog2(i) 

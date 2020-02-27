from pymtl3 import *

class CacheDataReplicator( Component ):

  def construct( s , p ):

    s.msg_len = InPort (p.BitsLen)
    s.data    = InPort (p.BitsData)
    s.out     = OutPort(p.BitsCacheline)

    @s.update
    def replicator(): 
      if s.msg_len == 1: 
        for i in range(0,p.bitwidth_cacheline,8): # byte
          s.out[i:i+8] = s.data
      elif s.msg_len == 2:
        for i in range(0,p.bitwidth_cacheline,16): # half word
          s.out[i:i+16] = s.data
      else:
        for i in range(0,p.bitwidth_cacheline,p.bitwidth_data):
          s.out[i:i+p.bitwidth_data] = s.data
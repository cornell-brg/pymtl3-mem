from pymtl3 import *

class CacheDataReplicator( Component ):

  def construct( s , p ):

    s.msg_len = InPort (p.BitsLen)
    s.data    = InPort (p.BitsData)
    s.out     = OutPort(p.BitsCacheline)

    BitsLen            = p.BitsLen
    bitwidth_cacheline = p.bitwidth_cacheline
    bitwidth_data      = p.bitwidth_data

    @s.update
    def replicator(): 
      if s.msg_len == BitsLen(1): 
        for i in range( 0, bitwidth_cacheline, 8 ): # byte
          s.out[i:i+8] = s.data[0:8]
      elif s.msg_len == BitsLen(2):
        for i in range( 0, bitwidth_cacheline, 16 ): # half word
          s.out[i:i+16] = s.data[0:16]
      else:
        for i in range( 0, bitwidth_cacheline, bitwidth_data ):
          s.out[i:i+bitwidth_data] = s.data

from pymtl3 import *

# N-input Mux
class PMux( Component ):

  def construct( s, Type, ninputs ):

    s.in_ = [ InPort( Type ) for _ in range(ninputs) ]
    s.out = OutPort( Type )

    if ninputs > 1:
      s.sel = InPort( int if Type is int else mk_bits( clog2(ninputs) ) )
      @s.update
      def up_mux():
        s.out = s.in_[ s.sel ]

    else:
      s.sel = InPort ( Bits1 )
      @s.update
      def up_mux():
        s.out = s.in_[ b1(0) ]

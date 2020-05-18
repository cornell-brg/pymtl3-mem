module SramGenericPRTL
 #(parameter num_bits=128 , parameter num_words=256)
(
  input logic [($clog2(num_words))-1:0] A1 ,
  input logic [0:0] CE1 ,
  input logic [0:0] CSB1 ,
  input logic [num_bits-1:0] I1 ,
  output logic [num_bits-1:0] O1 ,
  input logic [0:0] OEB1 ,
  input logic [num_bits-1:0] WBM1 ,
  input logic [0:0] WEB1 ,
  input logic [0:0] clk ,
  input logic [0:0] reset 
);

  localparam logic [31:0] __const__nbytes_at_write_logic  = (num_bits/8);
 
  localparam logic [31:0] __const__num_words_at_write_logic  = num_words;
  localparam logic [31:0] __const__num_bits_at_write_logic  = num_bits;
  localparam logic [31:0] __const__num_words_at_update_sram  = num_words;

  wire ceny;
  wire [num_bits-1:0] weny;
  wire [$clog2(num_words)-1:0] ay;
  wire gweny;
  wire [1:0] so;
  wire brg_ceny;
  wire [num_bits-1:0] brg_weny;
  wire [$clog2(num_words)-1:0] brg_ay;
  wire brg_gweny;
  logic [num_bits-1:0] q;
  wire [1:0] brg_so;

  wire  cen;
  wire [num_bits-1:0] wen;
  wire [$clog2(num_words)-1:0] a;
  wire [num_bits-1:0] d;
  wire [2:0] ema;
  wire [1:0] emaw;
  wire  emas;
  wire  ten;
  wire  tcen;
  wire [num_bits-1:0] twen;
  wire [$clog2(num_words)-1:0] ta;
  wire [num_bits-1:0] td;
  wire  gwen;
  wire  tgwen;
  wire  ret1n;
  wire [1:0] si;
  wire  se;
  wire  dftrambyp;
  wire unused = reset;


  assign a = A1;
  assign d = I1;
//  assign O1 = q;
  assign gwen = WEB1;
  assign cen = CSB1;

  assign dftrambyp = 1'd0;
  assign ema = 3'd3;
  assign emas = 1'd0;
  assign emaw = 2'd1;
  assign ret1n = 1'd1;
  assign se = 1'd0;
  assign si = 2'd0;
  assign ta = {$clog2(num_words){1'b0}}; //8'd0;
  assign tcen = 1'd0;
  assign td = {num_bits{1'b0}}; //128'd0;
  assign ten = 1'd1;
  assign tgwen = 1'd0;
  assign twen = {num_bits{1'b0}}; //128'd0;

  assign brg_ceny = ceny;
  assign brg_weny = weny;
  assign brg_ay = ay;
  assign brg_gweny = gweny;
  assign brg_so = so;
  genvar j;
/*
  for(j = 0; j < __const__nbytes_at_write_logic; j++)
    assign wen[8*j+:8] = {8{WBM1[j]}};
*/
 assign  wen[num_bits-1:0] = WBM1[num_bits-1:0];

  if ((num_bits==128) && (num_words==256)) begin
 
    gf14_sram_256x128_m2 sram_256x128 (.ceny(ceny), .gweny(gweny), .ay(ay), .weny(weny), .q(q), .so(so), .clk(clk), .cen(cen), .gwen(gwen), .a(a), .d(d), .wen(~wen), .stov(1'b0), .ema(ema),
    .emaw(emaw), .emas(emas), .ten(ten), .tcen(tcen), .tgwen(tgwen), .ta(8'd0), .td(128'd0), .twen(128'd0), .si(si), .se(se), .dftrambyp(dftrambyp), .ret1n(ret1n));
  end
  else if ((num_bits==24) && (num_words==256)) begin
     gf14_sram_256x24_m4 sram_256x24 (.ceny(ceny), .gweny(gweny), .ay(ay), .q(q), .so(so), .clk(clk), .cen(cen), .gwen(gwen), .a(a), .d(d), .stov(1'b0), .ema(ema),
    .emaw(emaw), .emas(emas), .ten(ten), .tcen(tcen), .tgwen(tgwen), .ta(8'd0), .td(24'd0), .si(si), .se(se), .dftrambyp(dftrambyp), .ret1n(ret1n));
 
  end 
  else if ((num_bits==32) && (num_words==128)) begin
    gf14_sram_128x32_m2 sram_128x32 (.ceny(ceny), .gweny(gweny), .ay(ay), .weny(weny), .q(q), .so(so), .clk(clk), .cen(cen), .gwen(gwen), .a(a), .d(d), .wen(~wen), .stov(1'b0), .ema(ema), 
    .emaw(emaw), .emas(emas), .ten(ten), .tcen(tcen), .tgwen(tgwen), .ta(7'd0), .td(32'd0), .twen(32'd0), .si(si), .se(se), .dftrambyp(dftrambyp), .ret1n(ret1n));
  end
 else if ((num_bits==26) && (num_words==128)) begin
    gf14_sram_128x26_m2 sram_128x26 (.ceny(ceny), .gweny(gweny), .ay(ay), .weny(weny), .q(q), .so(so), .clk(clk), .cen(cen), .gwen(gwen), .a(a), .d(d), .wen(~wen), .stov(1'b0), .ema(ema),
    .emaw(emaw), .emas(emas), .ten(ten), .tcen(tcen), .tgwen(tgwen), .ta(7'd0), .td(26'd0), .twen(26'd0), .si(si), .se(se), .dftrambyp(dftrambyp), .ret1n(ret1n));
  end

  else begin
  // Do not find a hard SRAM, then use the behavioral model
  logic [num_bits-1:0] dout_next;
  logic [num_bits-1:0] ram [0:num_words-1];
  logic [num_bits-1:0] ram_next [0:num_words-1];

    always_comb begin : read_logic
      if ( ( !CSB1 ) && WEB1 ) begin
        dout_next = ram[A1];
      end
      else
        dout_next = 0;
    end
  
    always_comb begin : write_logic
      for ( int i = 0; i < __const__nbytes_at_write_logic; i += 1 )
        if ( ( !CSB1 ) && ( !WEB1 ) && WBM1[i] ) begin
          ram_next[A1][i * 8 +: 8] = I1[i * 8 +: 8];
        end
        else
          ram_next[A1][i * 8 +: 8] = ram[A1][i * 8 +: 8];
    end
    always_ff @(posedge clk) begin : update_sram
      q <= dout_next;
      if ( ( !CSB1 ) && ( !WEB1 ) ) begin
        for ( int i = 0; i < __const__num_words_at_update_sram; i += 1 )
          ram[i] <= ram_next[i];
      end
    end

  end


// Enable the output
 always_comb begin : comb_logic
    if ( !OEB1 ) begin
      O1 = q;
    end
    else
      O1 = 0;
  end

endmodule


module gf14_sram_256x128_m2 (ceny, gweny, ay, weny, q, so, clk, cen, gwen, a, d, wen,
    stov, ema, emaw, emas, ten, tcen, tgwen, ta, td, twen, si, se, dftrambyp, ret1n);

  output  ceny;
  output  gweny;
  output [7:0] ay;
  output [127:0] weny;
  output [127:0] q;
  output [1:0] so;
  input  clk;
  input  cen;
  input  gwen;
  input [7:0] a;
  input [127:0] d;
  input [127:0] wen;
  input  stov;
  input [2:0] ema;
  input [1:0] emaw;
  input  emas;
  input  ten;
  input  tcen;
  input  tgwen;
  input [7:0] ta;
  input [127:0] td;
  input [127:0] twen;
  input [1:0] si;
  input  se;
  input  dftrambyp;
  input  ret1n;

// synopsys translate_off 

  localparam logic [31:0] __const__num_words_at_write_logic  = 32'd256;
  localparam logic [31:0] __const__num_bits_at_write_logic  = 32'd128;
  localparam logic [31:0] __const__num_words_at_update_sram  = 32'd256;
  logic [127:0] ram [0:255];
  logic [127:0] ram_next [0:255];
  logic [127:0] dout_next;
  reg [127:0] q; 
  always_comb begin : read_logic
    if ( ( !cen ) && gwen ) begin
      dout_next = ram[a];
    end
    else
      dout_next = 128'd0;
  end

always_comb begin : write_logic
    for ( int i = 0; i < __const__num_words_at_write_logic; i += 1 )
      ram_next[i] = ram[i];
    for ( int i = 0; i < __const__num_bits_at_write_logic; i += 1 )
      if ( ( !cen ) && ( !gwen ) && (!wen[i]) ) begin
        ram_next[a][i] = d[i];
      end
  end
  always_ff @(posedge clk) begin : update_sram
    q <= dout_next;
    if ( ( !cen ) && ( !gwen ) ) begin
      for ( int i = 0; i < __const__num_words_at_update_sram; i += 1 )
        ram[i] <= ram_next[i];
    end
  end
// synopsys translate_on
endmodule


module gf14_sram_256x24_m4 (ceny, gweny, ay, q, so, clk, cen, gwen, a, d, stov, ema,
    emaw, emas, ten, tcen, tgwen, ta, td, si, se, dftrambyp, ret1n);
  output  ceny;
  output  gweny;
  output [7:0] ay;
  output [23:0] q;
  output [1:0] so;
  input  clk;
  input  cen;
  input  gwen;
  input [7:0] a;
  input [23:0] d;
  input  stov;
  input [2:0] ema;
  input [1:0] emaw;
  input  emas;
  input  ten;
  input  tcen;
  input  tgwen;
  input [7:0] ta;
  input [23:0] td;
  input [1:0] si;
  input  se;
  input  dftrambyp;
  input  ret1n;
// synopsys translate_off
  localparam logic [31:0] __const__nbytes_at_write_logic  = 32'd3;
  localparam logic [31:0] __const__num_words_at_update_sram  = 32'd256;
  logic [23:0] dout;
  logic [23:0] dout_next;
  logic [23:0] ram [0:255];
  logic [23:0] ram_next [0:255];
  reg [23:0] q;


  always_comb begin : read_logic
    if ( ( !cen ) && gwen ) begin
      dout_next = ram[a];
    end
    else
      dout_next = 24'd0;
  end
// NO BIT MASK!
  always_comb begin : write_logic
    for ( int i = 0; i < __const__nbytes_at_write_logic; i += 1 )
      if ( ( !cen) && ( !gwen ) ) begin
        ram_next[a][i * 8 +: 8] = d[i * 8 +: 8];
      end
      else
        ram_next[a][i * 8 +: 8] = ram[a][i * 8 +: 8];
  end

  always_ff @(posedge clk) begin : update_sram
    q <= dout_next;
    if ( ( !cen ) && ( !gwen ) ) begin
      for ( int i = 0; i < __const__num_words_at_update_sram; i += 1 )
        ram[i] <= ram_next[i];
    end
  end
// synopsys translate_on
endmodule

module gf14_sram_128x32_m2 (ceny, gweny, ay, weny, q, so, clk, cen, gwen, a, d, wen,
    stov, ema, emaw, emas, ten, tcen, tgwen, ta, td, twen, si, se, dftrambyp, ret1n);

  output  ceny;
  output  gweny;
  output [6:0] ay;
  output [31:0] weny;
  output [31:0] q;
  output [1:0] so;
  input  clk;
  input  cen;
  input  gwen;
  input [6:0] a;
  input [31:0] d;
  input [31:0] wen;
  input  stov;
  input [2:0] ema;
  input [1:0] emaw;
  input  emas;
  input  ten;
  input  tcen;
  input  tgwen;
  input [6:0] ta;
  input [31:0] td;
  input [31:0] twen;
  input [1:0] si;
  input  se;
  input  dftrambyp;
  input  ret1n;


// synopsys translate_off
  localparam logic [31:0] __const__num_words_at_write_logic  = 32'd128;
  localparam logic [31:0] __const__num_bits_at_write_logic  = 32'd32;
  localparam logic [31:0] __const__num_words_at_update_sram  = 32'd128;
  logic [31:0] dout;
  logic [31:0] dout_next;
  logic [31:0] ram [0:127];
  logic [31:0] ram_next [0:127];
  reg [31:0] q;


  always_comb begin : read_logic
    if ( ( !cen ) && gwen ) begin
      dout_next = ram[a];
    end
    else
      dout_next = 32'd0;
  end

  always_comb begin : write_logic
    for ( int i = 0; i < __const__num_words_at_write_logic; i += 1 )
      ram_next[i] = ram[i];
    for ( int i = 0; i < __const__num_bits_at_write_logic; i += 1 )
      if ( ( !cen ) && ( !gwen ) && (!wen[i]) ) begin
        ram_next[a][i] = d[i];
      end
  end

  always_ff @(posedge clk) begin : update_sram
    q <= dout_next;
    if ( ( !cen ) && ( !gwen ) ) begin
      for ( int i = 0; i < __const__num_words_at_update_sram; i += 1 )
        ram[i] <= ram_next[i];
    end
  end

// synopsys translate_on
endmodule

module gf14_sram_128x26_m2 (ceny, gweny, ay, weny, q, so, clk, cen, gwen, a, d, wen,
    stov, ema, emaw, emas, ten, tcen, tgwen, ta, td, twen, si, se, dftrambyp, ret1n);

  output  ceny;
  output  gweny;
  output [6:0] ay;
  output [25:0] weny;
  output [25:0] q;
  output [1:0] so;
  input  clk;
  input  cen;
  input  gwen;
  input [6:0] a;
  input [25:0] d;
  input [25:0] wen;
  input  stov;
  input [2:0] ema;
  input [1:0] emaw;
  input  emas;
  input  ten;
  input  tcen;
  input  tgwen;
  input [6:0] ta;
  input [25:0] td;
  input [25:0] twen;
  input [1:0] si;
  input  se;
  input  dftrambyp;
  input  ret1n;


// synopsys translate_off
  localparam logic [31:0] __const__num_words_at_write_logic  = 32'd128;
  localparam logic [31:0] __const__num_bits_at_write_logic  = 32'd26;
  localparam logic [31:0] __const__num_words_at_update_sram  = 32'd128;
  logic [25:0] dout;
  logic [25:0] dout_next;
  logic [25:0] ram [0:127];
  logic [25:0] ram_next [0:127];
  reg [25:0] q;


  always_comb begin : read_logic
    if ( ( !cen ) && gwen ) begin
      dout_next = ram[a];
    end
    else
      dout_next = 26'd0;
  end

  always_comb begin : write_logic
    for ( int i = 0; i < __const__num_words_at_write_logic; i += 1 )
      ram_next[i] = ram[i];
    for ( int i = 0; i < __const__num_bits_at_write_logic; i += 1 )
      if ( ( !cen ) && ( !gwen ) && (!wen[i]) ) begin
        ram_next[a][i] = d[i];
      end
  end

  always_ff @(posedge clk) begin : update_sram
    q <= dout_next;
    if ( ( !cen ) && ( !gwen ) ) begin
      for ( int i = 0; i < __const__num_words_at_update_sram; i += 1 )
        ram[i] <= ram_next[i];
    end
  end

// synopsys translate_on
endmodule

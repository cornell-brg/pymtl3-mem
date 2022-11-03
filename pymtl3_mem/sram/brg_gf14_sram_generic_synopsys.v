//========================================================================
// SRAM wrappers
//========================================================================
// Author: Shady Agwa
// Date: May 2020

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

  wire  cen;
  wire rdwen;
  wire [$clog2(num_words)-1:0] a;
  wire [num_bits-1:0] d;
  wire [num_bits-1:0] bw;
  logic [num_bits-1:0] q;

  localparam logic [31:0] __const__nbytes_at_write_logic  = (num_bits/8);
  localparam logic [31:0] __const__num_words_at_write_logic  = num_words;
  localparam logic [31:0] __const__num_bits_at_write_logic  = num_bits;
  localparam logic [31:0] __const__num_words_at_update_sram  = num_words;

  assign a = A1;
  assign d = I1;
  assign rdwen = WEB1; // READ Active High & Write Active Low
  assign cen = CSB1;  // CSB1 Active Low
  assign bw = WBM1;  // WBM1 Active High

  if ((num_bits==128) && (num_words==256)) begin
    gf14_sram_256x128 brg_sram_256x128 (.clk(clk), .cen(cen), .rdwen(rdwen), .a(a), .d(d), .bw(bw), .q(q));
  end
  else if((num_bits==26) && (num_words==128)) begin
    gf14_sram_128x26 brg_sram_128x26 (.clk(clk), .cen(cen), .rdwen(rdwen), .a(a), .d(d), .bw(bw), .q(q));
  end
  else if((num_bits==128) && (num_words==512)) begin
    gf14_sram_512x128 brg_sram_512x128 (.clk(clk), .cen(cen), .rdwen(rdwen), .a(a), .d(d), .bw(bw), .q(q));
  end
  else if((num_bits==25) && (num_words==256)) begin
    gf14_sram_256x25 brg_sram_256x25 (.clk(clk), .cen(cen), .rdwen(rdwen), .a(a), .d(d), .bw(bw), .q(q));
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
      for ( int i = 0; i < __const__num_words_at_write_logic; i += 1 )
        ram_next[i] = ram[i];
      for ( int i = 0; i < __const__num_bits_at_write_logic; i += 1 )
        if ( ( !CSB1 ) && ( !WEB1 ) && WBM1[i] ) begin // Bit Mask
          ram_next[A1][i] = I1[i];
        end
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

module gf14_sram_256x128
   (
    input  clk,
    input  cen,
    input  rdwen,
    input  [7:0] a,
    input  [127:0] d,
    input  [127:0] bw,
    output [127:0] q
    );

   sram_256x128 R1PB
     (
      .CLK         (clk),
      .CEN         (cen),
      .RDWEN       (rdwen),
      .A           (a),
      .D           (d),
      .BW          (bw),
      .T_LOGIC     (1'b0),
      .T_Q_RST     (1'b0),
      .MA_SAWL     (1'b0),
      .MA_WL       (1'b0),
      .MA_VD1      (1'b0),
      .MA_VD0      (1'b0),
      .MA_WRT      (1'b0),
      .Q           (q),
      .OBSV_CTL    ()
     );

endmodule

module gf14_sram_512x128
   (
    input  clk,
    input  cen,
    input  rdwen,
    input  [8:0] a,
    input  [127:0] d,
    input  [127:0] bw,
    output [127:0] q
    );

   sram_512x128 R1PB
     (
      .CLK         (clk),
      .CEN         (cen),
      .RDWEN       (rdwen),
      .A           (a),
      .D           (d),
      .BW          (bw),
      .T_LOGIC     (1'b0),
      .T_Q_RST     (1'b0),
      .MA_SAWL     (1'b0),
      .MA_WL       (1'b0),
      .MA_VD1      (1'b0),
      .MA_VD0      (1'b0),
      .MA_WRT      (1'b0),
      .Q           (q),
      .OBSV_CTL    ()
     );

endmodule

module gf14_sram_128x26
   (
    input  clk,
    input  cen,
    input  rdwen,
    input  [6:0] a,
    input  [25:0] d,
    input  [25:0] bw,
    output [25:0] q
    );

   sram_128x26 R1PB
     (
      .CLK         (clk),
      .CEN         (cen),
      .RDWEN       (rdwen),
      .A           (a),
      .D           (d),
      .BW          (bw),
      .T_LOGIC     (1'b0),
      .T_Q_RST     (1'b0),
      .MA_SAWL     (1'b0),
      .MA_WL       (1'b0),
      .MA_VD1      (1'b0),
      .MA_VD0      (1'b0),
      .MA_WRT      (1'b0),
      .Q           (q),
      .OBSV_CTL    ()
     );

endmodule

module gf14_sram_256x25
   (
    input  clk,
    input  cen,
    input  rdwen,
    input  [7:0] a,
    input  [24:0] d,
    input  [24:0] bw,
    output [24:0] q
    );

   sram_256x25 R1PB
     (
      .CLK         (clk),
      .CEN         (cen),
      .RDWEN       (rdwen),
      .A           (a),
      .D           (d),
      .BW          (bw),
      .T_LOGIC     (1'b0),
      .T_Q_RST     (1'b0),
      .MA_SAWL     (1'b0),
      .MA_WL       (1'b0),
      .MA_VD1      (1'b0),
      .MA_VD0      (1'b0),
      .MA_WRT      (1'b0),
      .Q           (q),
      .OBSV_CTL    ()
     );

endmodule

//------------------------------------------------------------------------
// Behavior models
//------------------------------------------------------------------------
// Behavior models for gf14_sram_256x128 and gf14_sram_128x26. Should be
// replaced with real SRAM cells in ASIC flows

// synopsys translate_off

module sram_128x26
(
   input logic CLK,
   input logic CEN,
   input logic RDWEN,
   input logic [6:0] A,
   input logic [25:0] D,
   input logic [25:0] BW,
   input logic T_LOGIC,
   input logic T_Q_RST,
   output logic [25:0] Q,
   output logic [1:0] OBSV_CTL,
   input logic MA_SAWL,
   input logic MA_WL,
   input logic MA_VD1,
   input logic MA_VD0,
   input logic MA_WRT

);

  logic [25:0] dout_next;
  logic [25:0] ram [0:127];
  logic [25:0] ram_next [0:127];

  always_comb begin : read_logic
    if ( ( !CEN ) && RDWEN ) begin
      dout_next = ram[A];
    end
    else
      dout_next = 0;
  end

  always_comb begin : write_logic
    for ( int i = 0; i < 128; i += 1 )
      ram_next[i] = ram[i];
    for ( int i = 0; i < 26; i += 1 )
      if ( ( !CEN ) && ( !RDWEN ) && BW[i] ) begin // Bit Mask
        ram_next[A][i] = D[i];
      end
  end

  always_ff @(posedge CLK) begin : update_sram
    Q <= dout_next;
    if ( ( !CEN ) && ( !RDWEN ) ) begin
      for ( int i = 0; i < 128; i += 1 )
        ram[i] <= ram_next[i];
    end
  end

endmodule

module sram_256x128
(
   input logic CLK,
   input logic CEN,
   input logic RDWEN,
   input logic [7:0] A,
   input logic [127:0] D,
   input logic [127:0] BW,
   input logic T_LOGIC,
   input logic T_Q_RST,
   output logic [127:0] Q,
   output logic [1:0] OBSV_CTL,
   input logic MA_SAWL,
   input logic MA_WL,
   input logic MA_VD1,
   input logic MA_VD0,
   input logic MA_WRT
);

  logic [127:0] dout_next;
  logic [127:0] ram [0:255];
  logic [127:0] ram_next [0:255];

  always_comb begin : read_logic
    if ( ( !CEN ) && RDWEN) begin
      dout_next = ram[A];
    end
    else
      dout_next = 0;
  end

  always_comb begin : write_logic
    for ( int i = 0; i < 256; i += 1 )
      ram_next[i] = ram[i];
    for ( int i = 0; i < 128; i += 1 )
      if ( ( !CEN ) && ( !RDWEN ) && BW[i] ) begin // Bit Mask
        ram_next[A][i] = D[i];
      end
  end

  always_ff @(posedge CLK) begin : update_sram
    Q <= dout_next;
    if ( ( !CEN ) && ( !RDWEN ) ) begin
      for ( int i = 0; i < 256; i += 1 )
        ram[i] <= ram_next[i];
    end
  end

endmodule

// synopsys translate_on

`timescale 1ns/1ps
// n-bit residues: reset displays 0; first non-reset edge displays 1.
module prep140_mod #(parameter integer W=8)
  (input wire clk,rst, output reg [W-1:0] square,
   output reg [W-1:0] odd);
  always @(posedge clk) begin
    if(rst) begin square<=0; odd<=1; end
    else begin square<=square+odd; odd<=odd+2; end
  end
endmodule

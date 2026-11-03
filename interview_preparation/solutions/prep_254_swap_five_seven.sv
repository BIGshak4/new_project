`timescale 1ns/1ps
module prep254(input wire [2:0] x, output wire [2:0] y);
  assign y = {x[2], x[1] ^ (x[2] & x[0]), x[0]};
endmodule

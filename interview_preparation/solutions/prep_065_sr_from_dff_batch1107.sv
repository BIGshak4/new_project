`timescale 1ns/1ps
// These are two ALTERNATIVE one-DFF implementations, not one alternating SR cell.
module prep065_set_priority(input wire clk, rst, s, r, output reg q);
  always @(posedge clk)
    if (rst) q <= 1'b0;
    else q <= s | (q & ~r);
endmodule

module prep065_reset_priority(input wire clk, rst, s, r, output reg q);
  always @(posedge clk)
    if (rst) q <= 1'b0;
    else q <= ~r & (s | q);
endmodule

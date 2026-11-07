`timescale 1ns/1ps
// N >= 1. This combinational fold saturates at three; it is not a serial counter.
module prep263 #(parameter integer N=8)
  (input wire [N-1:0] x, output wire y);
  reg [1:0] count;
  integer i;
  always @* begin
    count = 2'd0;
    for (i=0; i<N; i=i+1)
      if (x[i] && count != 2'd3) count = count + 2'd1;
  end
  assign y = (count == 2'd3);
endmodule

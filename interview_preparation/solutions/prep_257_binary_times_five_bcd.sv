`timescale 1ns/1ps
// All sixteen ordinary-binary inputs are legal; result range is 0..75.
module prep257(input wire [3:0] x,
               output wire [3:0] tens, ones);
  reg [6:0] product;
  reg [7:0] bcd;
  integer i;
  always @* begin
    product = ({3'b000,x} << 2) + {3'b000,x};
    bcd = 8'd0;
    for (i=6; i>=0; i=i-1) begin
      if (bcd[3:0] >= 5) bcd[3:0] = bcd[3:0] + 4'd3;
      if (bcd[7:4] >= 5) bcd[7:4] = bcd[7:4] + 4'd3;
      bcd = {bcd[6:0],product[i]};
    end
  end
  assign tens = bcd[7:4];
  assign ones = bcd[3:0];
endmodule

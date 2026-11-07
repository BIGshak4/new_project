`timescale 1ns/1ps
// Source range is 0..32 even though the input bus can encode 0..63.
module prep262(input wire [5:0] x,
               output reg valid, output reg [3:0] tens, ones);
  reg [7:0] bcd;
  integer i;
  always @* begin
    bcd = 0;
    for (i=5; i>=0; i=i-1) begin
      if (bcd[3:0] >= 5) bcd[3:0] = bcd[3:0] + 4'd3;
      if (bcd[7:4] >= 5) bcd[7:4] = bcd[7:4] + 4'd3;
      bcd = {bcd[6:0],x[i]};
    end
    valid = (x <= 6'd32);
    tens = valid ? bcd[7:4] : 4'd0;
    ones = valid ? bcd[3:0] : 4'd0;
  end
endmodule

// Exact unsigned product; fixed shifts are wiring after explicit extension.
module prep293_times49(input wire [9:0] x, output wire [15:0] y);
  wire [11:0] x12 = {2'b0,x};
  wire [11:0] three = (x12 << 1) + x12;
  assign y = {three,4'b0} + {6'b0,x};
endmodule

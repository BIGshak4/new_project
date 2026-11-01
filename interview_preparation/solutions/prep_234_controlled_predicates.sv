module controlled_predicates(input wire [3:0] x, input wire [1:0] mode, output wire y);
  wire any_zero = ~&x;
  wire majority = (x[3]&x[2]&x[1]) | (x[3]&x[2]&x[0]) |
                  (x[3]&x[1]&x[0]) | (x[2]&x[1]&x[0]);
  wire odd = ^x;
  assign y = mode == 2'b00 ? any_zero : mode == 2'b01 ? majority :
             mode == 2'b10 ? odd : ~odd;
endmodule

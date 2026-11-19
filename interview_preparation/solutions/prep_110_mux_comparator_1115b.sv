// Every ternary conditional below denotes one two-to-one multiplexer.
module prep110_mux(input wire [1:0] a,b, output wire greater);
  wire not_b0 = b[0] ? 1'b0 : 1'b1;
  wire low_greater = a[0] ? not_b0 : 1'b0;
  wire when_a1_zero = b[1] ? 1'b0 : low_greater;
  wire when_a1_one = b[1] ? low_greater : 1'b1;
  assign greater = a[1] ? when_a1_one : when_a1_zero;
endmodule

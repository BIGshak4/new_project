module prep018_minmax8(input wire [7:0] a,b,
                      output wire [7:0] maximum,minimum);
  wire swap = a < b;
  assign maximum = swap ? b : a;
  assign minimum = swap ? a : b;
endmodule

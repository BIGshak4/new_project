`timescale 1ns/1ps
// Primary source reading: a new bit is inserted at the right/LSB, N'=2*N+b.
// The remainder is sufficient for unbounded word lengths; seen qualifies empty.
module prep206_append_lsb_seven(input wire clk, rst, bit_valid, bit_in,
                               output wire divisible);
  reg [2:0] remainder;
  reg seen;
  wire [3:0] candidate={remainder,bit_in};
  always @(posedge clk) begin
    if (rst) begin remainder<=0; seen<=0; end
    else if (bit_valid) begin
      remainder <= candidate >= 4'd7 ? candidate-4'd7 : candidate;
      seen <= 1;
    end
  end
  assign divisible=seen && (remainder==0);
endmodule

// Separate alternative: the lowest-weight bit arrives first, N'=N+b*2^k.
// phase tracks k modulo3 because powers of two modulo7 repeat 1,2,4.
module prep206_lsb_first_seven(input wire clk, rst, bit_valid, bit_in,
                              output wire divisible);
  reg [2:0] remainder;
  reg [1:0] phase;
  reg seen;
  wire [2:0] weight = phase==0 ? 3'd1 : (phase==1 ? 3'd2 : 3'd4);
  wire [3:0] candidate = {1'b0,remainder} + (bit_in ? {1'b0,weight} : 4'd0);
  always @(posedge clk) begin
    if (rst) begin remainder<=0; phase<=0; seen<=0; end
    else if (bit_valid) begin
      remainder <= candidate >= 4'd7 ? candidate-4'd7 : candidate;
      phase <= phase==2 ? 2'd0 : phase+2'd1;
      seen <= 1;
    end
  end
  assign divisible=seen && (remainder==0);
endmodule

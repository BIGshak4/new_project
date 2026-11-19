`timescale 1ns/1ps
// Legal simulation transcription. The redundant reg declaration of Out is removed.
module prep044_source(input wire clk, rst, enable, output wire [15:0] Out);
  reg [15:0] X, Y;
  always @(posedge clk or negedge rst)
    if (!rst) X <= #1 16'b0;
    else if (enable == 1'b1) X <= #1 Y;
  always @(posedge clk or negedge rst)
    if (!rst) Y <= #1 16'b1;
    else if (enable == 1'b1) Y <= #1 Out;
  assign Out = X + Y;
endmodule

// Synthesizable intent, preserving the same enable/reset and arithmetic widths.
module prep044_rtl(input wire clk, rst, enable, output wire [15:0] Out);
  reg [15:0] X, Y;
  always @(posedge clk or negedge rst) begin
    if (!rst) begin X <= 16'b0; Y <= 16'b1; end
    else if (enable) begin X <= Y; Y <= X + Y; end
  end
  assign Out = X + Y;
endmodule

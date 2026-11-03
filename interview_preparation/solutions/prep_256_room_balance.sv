`timescale 1ns/1ps
// Bounded occupancy contract: abs(men-women) <= CAPACITY for legal histories.
module prep256 #(parameter integer CAPACITY=8,
                 parameter integer W=$clog2(CAPACITY+1)+1)
  (input wire clk, rst, input wire [3:0] event_code,
   output wire red, green, blue, output reg signed [W-1:0] difference);
  always @(posedge clk) begin
    if (rst) difference <= 0;
    else case (event_code)
      4'b0100, 4'b0010: difference <= difference + 1;
      4'b1000, 4'b0001: difference <= difference - 1;
      default: difference <= difference; // none; invalid words hold by choice
    endcase
  end
  assign red = difference > 0;
  assign green = difference == 0;
  assign blue = difference < 0;
endmodule

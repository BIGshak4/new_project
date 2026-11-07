`timescale 1ns/1ps
module prep206_serial_four_batch1107b10(
 input logic clk,rst,bit_valid,bit_in, output logic divisible);
 logic [1:0] suffix;
 logic seen;
 always @(posedge clk) begin
   if(rst) begin suffix<=0; seen<=0; end
   else if(bit_valid) begin suffix<={suffix[0],bit_in}; seen<=1; end
 end
 assign divisible=seen && (suffix==2'b00);
endmodule

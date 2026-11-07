`timescale 1ns/1ps
module prep095_recent_one_batch1107b10 #(parameter integer WINDOW=1000)(
 input logic clk,rst,x, output logic y);
 localparam integer CW=$clog2(WINDOW+1);
 logic [CW-1:0] remaining;
 always @(posedge clk) begin
   if(rst) remaining<=0;
   else if(x) remaining<=WINDOW;
   else if(remaining!=0) remaining<=remaining-1'b1;
 end
 assign y=(remaining!=0);
endmodule

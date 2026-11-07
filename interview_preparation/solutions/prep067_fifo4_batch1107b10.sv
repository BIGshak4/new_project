`timescale 1ns/1ps
module prep067_fifo4_batch1107b10 #(parameter integer W=8)(
 input logic clk,rst,in_valid,out_ready,
 input logic [W-1:0] in_data,
 output wire in_ready,out_valid,
 output wire [W-1:0] out_data);
 logic [W-1:0] mem[0:3];
 logic [1:0] rptr,wptr;
 logic [2:0] count;
 wire pop=out_valid && out_ready;
 wire push=in_valid && in_ready;
 assign out_valid=(count!=0);
 assign in_ready=(count<4)||pop;
 assign out_data=mem[rptr];
 always @(posedge clk) begin
   if(rst) begin count<=0; rptr<=0; wptr<=0; end
   else begin
     if(push) begin mem[wptr]<=in_data; wptr<=wptr+1'b1; end
     if(pop) rptr<=rptr+1'b1;
     case({push,pop})
       2'b10:count<=count+1'b1;
       2'b01:count<=count-1'b1;
       default:count<=count;
     endcase
   end
 end
endmodule

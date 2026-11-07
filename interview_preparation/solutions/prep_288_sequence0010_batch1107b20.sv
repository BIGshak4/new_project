`timescale 1ns/1ps
// Four proper-prefix states plus one registered event output.
module prep288_sequence0010_batch1107b20(
 input wire clk,rst,bit_valid,bit_in,output reg found);
 reg [1:0] state;
 always @(posedge clk)begin
   if(rst)begin state<=0;found<=0;end
   else begin
     found<=0;
     if(bit_valid)begin
       found<=(state==3 && !bit_in);
       case(state)
         0:state<=bit_in?0:1;
         1:state<=bit_in?0:2;
         2:state<=bit_in?3:2;
         3:state<=bit_in?0:1;
       endcase
     end
   end
 end
endmodule

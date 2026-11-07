`timescale 1ns/1ps
module prep050_mod5_orders_batch1107b10(
 input logic clk,rst,bit_valid,bit_in,
 output wire msb_divisible,lsb_divisible);
 logic [2:0] msb_state,lsb_state;
 // Constant finite tables: no general-purpose hardware division.
 function automatic [2:0] msb_next(input [2:0] s,input b);
   case(s)
     0:msb_next=b?1:0; 1:msb_next=b?3:2;
     2:msb_next=b?0:4; 3:msb_next=b?2:1;
     4:msb_next=b?4:3; default:msb_next=0;
   endcase
 endfunction
 function automatic [2:0] lsb_next(input [2:0] s,input b);
   case(s)
     0:lsb_next=b?3:0; 1:lsb_next=b?1:3;
     2:lsb_next=b?4:1; 3:lsb_next=b?2:4;
     4:lsb_next=b?0:2; default:lsb_next=0;
   endcase
 endfunction
 always @(posedge clk) begin
   if(rst) begin msb_state<=0; lsb_state<=0; end
   else if(bit_valid) begin
     msb_state<=msb_next(msb_state,bit_in);
     lsb_state<=lsb_next(lsb_state,bit_in);
   end
 end
 assign msb_divisible=(msb_state==0);
 assign lsb_divisible=(lsb_state==0);
endmodule

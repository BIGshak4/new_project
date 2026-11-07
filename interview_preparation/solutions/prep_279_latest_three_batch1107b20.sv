`timescale 1ns/1ps
// Capture history first; combinational outputs sort the three latest values.
module prep279_latest_three_batch1107b20(
 input wire clk,rst,sample_valid,input wire [1:0] sample,
 output wire out_valid,output reg [1:0] minimum,middle,maximum);
 reg [1:0] h0,h1,h2,fill;
 reg [1:0] a,b,c,t;
 always @(posedge clk) begin
   if(rst) begin h0<=0;h1<=0;h2<=0;fill<=0;end
   else if(sample_valid) begin
     h2<=h1;h1<=h0;h0<=sample;
     if(fill<3) fill<=fill+1'b1;
   end
 end
 assign out_valid=(fill==3);
 always @* begin
   a=h0;b=h1;c=h2;t=0;
   if(a>b)begin t=a;a=b;b=t;end
   if(b>c)begin t=b;b=c;c=t;end
   if(a>b)begin t=a;a=b;b=t;end
   minimum=a;middle=b;maximum=c;
 end
endmodule

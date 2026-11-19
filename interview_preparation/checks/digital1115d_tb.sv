`timescale 1ns/1ps
module digital1115d_tb;
 reg clk=0,rst=0,x=0,hot=0,cold=0;
 wire hit,y1,y3,y8,fan,fault;
 reg [7:0] word;
 wire [7:0] mask;
 prep207_detect1010 seq(clk,rst,x,hit);
 prep014_weighted_msb msb(word,mask);
 prep042_stretch #(.N(1)) st1(clk,rst,x,y1);
 prep042_stretch #(.N(3)) st3(clk,rst,x,y3);
 prep042_stretch #(.N(8)) st8(clk,rst,x,y8);
 prep_thermal1115d th(clk,rst,hot,cold,fan,fault);
 integer i,j,k,t,code,b,expected_mask,checked=0;
 integer last_rise,previous,history,have,expected_hit,expected_fan;
 task tick;begin #5;clk=1;#2;clk=0;#3;end endtask
 initial begin
  for(i=0;i<256;i=i+1) begin
   word=i;#1;expected_mask=0;
   for(j=0;j<8;j=j+1)if((i>>j)&1)expected_mask=1<<j;
   if(mask!==expected_mask[7:0])$fatal(1,"MSB word=%0d got=%0d expected=%0d",i,mask,expected_mask);
   checked=checked+1;
  end
  // Exhaust every ten-sample stream. A second pass resets on sample five.
  for(t=0;t<2;t=t+1) for(i=0;i<1024;i=i+1) begin
   rst=1;x=0;hot=0;cold=0;tick();
   if(hit!==0||y1!==0||y3!==0||y8!==0||fan!==0)$fatal(1,"reset failed");
   last_rise=-1000;previous=0;history=0;have=0;
   for(k=0;k<10;k=k+1) begin
    rst=(t==1&&k==5);x=(i>>k)&1;
    if(rst) begin last_rise=-1000;previous=0;history=0;have=0;expected_hit=0;end
    else begin
     if(x&&!previous)last_rise=k;
     previous=x;history=((history<<1)|x)&15;have=have+1;
     expected_hit=(have>=4&&history==10);
    end
    tick();
    if(hit!==expected_hit[0])$fatal(1,"1010 stream=%0d k=%0d rst=%0d",i,k,rst);
    if(y1!==(k-last_rise<1)||y3!==(k-last_rise<3)||y8!==(k-last_rise<8))
     $fatal(1,"stretch stream=%0d k=%0d resetpass=%0d",i,k,t);
    checked=checked+4;
   end
  end
  // All five-control-pair streams, with/without reset in the middle.
  for(t=0;t<2;t=t+1)for(i=0;i<1024;i=i+1) begin
   rst=1;hot=0;cold=0;tick();expected_fan=0;
   for(k=0;k<5;k=k+1)begin
    rst=(t==1&&k==2);code=(i>>(2*k))&3;hot=(code>>1)&1;cold=code&1;
    if(rst||cold)expected_fan=0;
    else if(hot)expected_fan=1;
    tick();
    if(fan!==expected_fan[0]||fault!==(hot&cold))$fatal(1,"thermal stream=%0d k=%0d",i,k);
    checked=checked+2;
   end
  end
  $display("PASS digital1115d: assertions=%0d; msb=256; seq/stretch=20480 samples; thermal=10240 samples",checked);
  $finish;
 end
endmodule

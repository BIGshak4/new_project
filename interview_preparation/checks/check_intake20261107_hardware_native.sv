`timescale 1ns/1ps
module tb;
  reg [3:0] x4;
  wire [3:0] t5,u5;
  reg [5:0] x6;
  wire [3:0] td,ud;
  wire v;
  reg [11:0] bits;
  wire [11:0] threshold;
  reg clk=0, rst=0, s=0, r=0, bit_valid=0, bit_in=0;
  wire qs,qr,lsb_first,append_lsb;
  integer i,n,oldq,a,b,word,k,c,expected,checks=0,accum,position;
  prep257 p257(x4,t5,u5);
  prep262 p262(x6,v,td,ud);
  genvar width;
  generate for(width=1;width<=12;width=width+1) begin:g
    prep263 #(.N(width)) p263(bits[width-1:0],threshold[width-1]);
  end endgenerate
  prep065_set_priority ps(clk,rst,s,r,qs);
  prep065_reset_priority pr(clk,rst,s,r,qr);
  prep206_lsb_first_seven pl(clk,rst,bit_valid,bit_in,lsb_first);
  prep206_append_lsb_seven pa(clk,rst,bit_valid,bit_in,append_lsb);
  task tick;
    begin #2;clk=1;#2;clk=0;#1; end
  endtask
  initial begin
    for(i=0;i<16;i=i+1) begin
      x4=i;#1;
      if(t5!=(i*5)/10 || u5!=(i*5)%10) $fatal(1,"257 x=%0d",i);
      checks=checks+1;
    end
    for(i=0;i<64;i=i+1) begin
      x6=i;#1;
      if(v!=(i<=32)) $fatal(1,"262 valid x=%0d",i);
      if(i<=32) begin
        if(td!=i/10 || ud!=i%10) $fatal(1,"262 digits x=%0d",i);
      end else if(td!=0 || ud!=0) $fatal(1,"262 invalid output");
      checks=checks+1;
    end
    for(word=0;word<4096;word=word+1) begin
      bits=word;#1;c=0;
      for(n=1;n<=12;n=n+1) begin
        if((word>>(n-1))&1) c=c+1;
        if(threshold[n-1]!=(c>2)) $fatal(1,"263 word=%0d n=%0d",word,n);
        checks=checks+1;
      end
    end
    for(oldq=0;oldq<2;oldq=oldq+1)
      for(a=0;a<2;a=a+1) for(b=0;b<2;b=b+1) begin
        rst=1;tick;rst=0;s=oldq;r=0;tick;
        s=a;r=b;tick;
        if(qs!=(a?1:(b?0:oldq))) $fatal(1,"065 set priority");
        if(qr!=(b?0:(a?1:oldq))) $fatal(1,"065 reset priority");
        checks=checks+2;
      end
    s=0;r=0;
    for(word=0;word<4096;word=word+1) begin
      rst=1;bit_valid=1;bit_in=1;tick;
      if(lsb_first || append_lsb) $fatal(1,"206 reset priority");
      rst=0;accum=0;expected=0;
      for(k=0;k<12;k=k+1) begin
        bit_in=(word>>k)&1;bit_valid=1;tick;
        accum=accum+(bit_in<<k);
        expected=2*expected+bit_in;
        if(lsb_first!=(accum%7==0)) $fatal(1,"206 first-weight word=%0d k=%0d",word,k);
        if(append_lsb!=(expected%7==0)) $fatal(1,"206 append word=%0d k=%0d",word,k);
        checks=checks+2;
        if((k%4)==0) begin
          bit_valid=0;bit_in=~bit_in;tick;
          if(lsb_first!=(accum%7==0) || append_lsb!=(expected%7==0)) $fatal(1,"206 valid hold");
          checks=checks+2;
        end
      end
    end
    $display("PASS hardware native checks=%0d (257,262,263,065,206)",checks);
    $finish;
  end
endmodule

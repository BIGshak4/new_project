`timescale 1ns/1ps
module tb_hardware_batch1107b20;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,valid=0,bit_in=0;reg [1:0] sample=0;
 wire ov;wire[1:0]mn,md,mx;
 wire found;reg a=0,b=0;wire x,y,yo,ym,yn,an,ar,am;
 prep279_latest_three_batch1107b20 u279(clk,rst,valid,sample,ov,mn,md,mx);
 prep282_ideal_switch_xor_batch1107b20 u282(a,b,y,x);
 prep283_implication_batch1107b20 u283(a,b,yo,ym,yn);
 prep286_and_bases_batch1107b20 u286(a,b,an,ar,am);
 prep288_sequence0010_batch1107b20 u288(clk,rst,valid,bit_in,found);
 integer checks=0,ai,bi,word,len,j,n,h0=0,h1=0,h2=0,fill=0;
 integer e0,e1,e2,tmp,history=0,seen=0,cycle;
 reg expected;
 task check(input reg okay);begin checks=checks+1;if(!okay)$fatal(1,"failed check %0d",checks);end endtask
 task tick;begin @(posedge clk);#1;end endtask
 initial begin
   tick;check(ov===0 && found===0);
   for(ai=0;ai<2;ai=ai+1)for(bi=0;bi<2;bi=bi+1)begin
     a=ai;b=bi;#1;check(x==!ai);check(y==(ai^bi));
     check(yo==(!ai||bi));check(ym==yo && yn==yo);
     check(an==(ai&&bi));check(ar==an && am==an);
   end
   // Independent numeric suffix oracle for all words through length 11.
   for(len=1;len<=11;len=len+1)for(word=0;word<(1<<len);word=word+1)begin
     @(negedge clk);rst=1;valid=0;tick;check(found===0);
     history=0;seen=0;
     for(j=0;j<len;j=j+1)begin
       @(negedge clk);rst=0;valid=0;bit_in=(word>>j)&1;
       tick;check(found===0);
       @(negedge clk);valid=1;history=((history<<1)|bit_in)&15;seen=seen+1;
       expected=(seen>=4 && history==2);
       tick;check(found===expected);
     end
   end
   @(negedge clk);rst=1;valid=0;tick;fill=0;
   // All triples + varied valid/reset traffic, compared to an independent sort.
   for(cycle=0;cycle<5256;cycle=cycle+1)begin
     @(negedge clk);
     rst=(cycle<256)?(cycle%4==0):(cycle%97==0);
     valid=(cycle<256)?1:(cycle%7!=0);
     sample=(cycle<256)?((cycle/4)>>(2*((cycle%4+3)%4)))&3:((cycle*17+cycle/3)%4);
     if(rst)begin h0=0;h1=0;h2=0;fill=0;end
     else if(valid)begin h2=h1;h1=h0;h0=sample;if(fill<3)fill=fill+1;end
     e0=h0;e1=h1;e2=h2;
     // Selection via min/max/multiset sum instead of DUT's exchange network.
     tmp=e0;if(e1<tmp)tmp=e1;if(e2<tmp)tmp=e2;
     n=e0;if(e1>n)n=e1;if(e2>n)n=e2;
     tick;check(ov==(fill==3));check(mn==tmp && mx==n && md==e0+e1+e2-tmp-n);
   end
   $display("PASS batch1107b20 hardware checks=%0d serial_words=4094 serial_prefixes=40962 history_cycles=5256 truth_rows=4",checks);
   $finish;
 end
endmodule

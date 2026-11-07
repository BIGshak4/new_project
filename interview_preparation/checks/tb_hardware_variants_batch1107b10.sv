`timescale 1ns/1ps
module tb_hardware_variants_batch1107b10;
 reg clk=0; always #5 clk=~clk;
 reg rst=1,x=0,valid=0,bit_in=0;
 wire recent,div4,div5m,div5l;
 reg [1:0] a=0,b=0; wire [1:0] mx;
 reg iv=0,orr=0; reg [7:0] din=0;
 wire ir,ov; wire [7:0] dout;
 prep095_recent_one_batch1107b10 u95(clk,rst,x,recent);
 prep206_serial_four_batch1107b10 u206(clk,rst,valid,bit_in,div4);
 prep050_mod5_orders_batch1107b10 u50(clk,rst,valid,bit_in,div5m,div5l);
 prep018_two_bit_max_batch1107b10 u18(a,b,mx);
 prep067_fifo4_batch1107b10 u67(clk,rst,iv,orr,din,ir,ov,dout);
 integer checks=0,cycle,last_one=-1001,n=0,lo=0,pos=0;
 integer pattern,length,j,ai,bi,qn=0,i;
 reg history[0:999]; reg want_recent;
 reg [7:0] queue[0:3]; reg do_push,do_pop;
 task check(input reg ok);
   begin checks=checks+1; if(!ok) $fatal(1,"check %0d failed",checks); end
 endtask
 task tick;
   begin @(posedge clk); #1; end
 endtask
 initial begin
   tick; check(recent===0 && div4===0 && div5m===1 && div5l===1);
   @(negedge clk); rst=0;
   for(ai=0;ai<4;ai=ai+1) for(bi=0;bi<4;bi=bi+1) begin
     a=ai;b=bi;#1;check(mx==(ai>bi?ai:bi));
   end
   // Exactly one pulse followed by a thousand zeros tests both expiry edges.
   for(cycle=0;cycle<1300;cycle=cycle+1) begin
     @(negedge clk); x=(cycle==0 || cycle==1100);
     if(x) last_one=cycle;
     tick; check(recent==((cycle-last_one)<1000));
   end
   // Exhaust every word through length 10, with idle cycles before each bit.
   for(length=1;length<=10;length=length+1)
     for(pattern=0;pattern<(1<<length);pattern=pattern+1) begin
       @(negedge clk); rst=1; valid=0; tick;
       check(div4===0 && div5m===1 && div5l===1);
       n=0;lo=0;pos=0;
       for(j=0;j<length;j=j+1) begin
         @(negedge clk); rst=0;valid=0;bit_in=(pattern>>j)&1;
         tick; check(div4==((pos>0)&&(n%4==0)));
         check(div5m==(n%5==0));check(div5l==(lo%5==0));
         @(negedge clk);valid=1;
         n=2*n+bit_in;lo=lo+bit_in*(1<<pos);pos=pos+1;
         tick;check(div4==(n%4==0));check(div5m==(n%5==0));check(div5l==(lo%5==0));
       end
     end
   @(negedge clk);rst=1;iv=0;orr=0;valid=0;tick;
   check(ov===0 && ir===1);
   @(negedge clk);rst=0;
   // Directed fill/full replacement/drain + deterministic varied traffic.
   for(cycle=0;cycle<5000;cycle=cycle+1) begin
     @(negedge clk);
     iv=(cycle<4)?1:((cycle<8)?1:((cycle*13+5)%7<5));
     orr=(cycle<4)?0:((cycle<12)?1:((cycle*17+2)%11<7));
     din=cycle;
     #1;check(ov==(qn>0));check(ir==((qn<4)||((qn>0)&&orr)));
     do_pop=(qn>0)&&orr;do_push=iv&&ir;
     if(qn>0) check(dout===queue[0]);
     if(do_pop) begin for(i=0;i<qn-1;i=i+1)queue[i]=queue[i+1]; qn=qn-1; end
     if(do_push) begin queue[qn]=din;qn=qn+1;end
     tick;check(ov==(qn>0));if(qn>0)check(dout===queue[0]);
   end
   $display("PASS hardware variants checks=%0d serial_words=2046 fifo_cycles=5000 window_cycles=1300 max_pairs=16",checks);
   $finish;
 end
endmodule

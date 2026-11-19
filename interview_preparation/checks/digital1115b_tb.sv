`timescale 1ns/1ps
module digital1115b_tb;
  reg [15:0] p=0; wire pv; wire [3:0] pc;
  prep349_pe16 pe(p,pv,pc);
  reg [1:0] ca=0,cb=0; wire gt;
  prep110_mux compare(ca,cb,gt);
  reg [7:0] aa=0; reg [8:0] bb=0; wire [8:0] mean;
  prep058_full_mean #(.W(8)) avg(aa,bb,mean);
  reg one_a=0; reg [1:0] one_b=2; wire [1:0] one_mean;
  prep058_full_mean #(.W(1)) avg_one(one_a,one_b,one_mean);
  reg clk=0,rst=1,start=0;reg [7:0] data=0;reg [2:0] amount=0;
  wire [7:0] result;wire busy,done;
  prep350 sh(clk,rst,start,data,amount,result,busy,done);
  reg fclk=0,frst=1,fen=0;wire [15:0] fout;
  prep044_source fib(fclk,frst,fen,fout);
  integer i,j,k,expected,mask,shift_checks=0,fib_checks=0;
  reg [7:0] saved;
  reg [15:0] fx=0,fy=1,oldout;
  task tick;
    begin #1;clk=1;#1;clk=0;#1;end
  endtask
  task fib_tick(input bit en);
    reg [15:0] nextx,nexty;
    begin
      fen=en;oldout=fx+fy;nextx=fx;nexty=fy;
      if (en)begin nextx=fy;nexty=fx+fy;end
      #2;fclk=1;#0.5;
      if (fout !== oldout)$fatal(1,"NBA delay changed output early");
      #0.6;fx=nextx;fy=nexty;
      if (fout !== ((fx+fy)&16'hffff))$fatal(1,"Fibonacci source mismatch");
      fclk=0;fib_checks=fib_checks+1;
    end
  endtask
  initial begin
    // Independent arithmetic highest-bit reference covers every 16-bit word.
    for(i=0;i<65536;i=i+1)begin
      p=i;#1;expected=0;
      for(j=0;j<16;j=j+1)if(i & (1<<j))expected=j;
      if(pv !== (i!=0) || pc !== expected[3:0])$fatal(1,"Priority encoder %0d",i);
    end
    for(i=0;i<4;i=i+1)for(j=0;j<4;j=j+1)begin
      ca=i;cb=j;#1;
      if(gt !== (i>j))$fatal(1,"Comparator %0d,%0d",i,j);
    end
    for(i=0;i<256;i=i+1)begin
      aa=i;bb=i+2;#1;
      if(mean !== ((2*i+2)/2))$fatal(1,"Carry mean %0d",i);
    end
    for(i=0;i<2;i=i+1)begin
      one_a=i;one_b=i+2;#1;
      if(one_mean !== (i+1))$fatal(1,"One-bit full-carry mean");
    end
    tick();rst=0;
    for(i=0;i<256;i=i+1)for(j=0;j<8;j=j+1)begin
      start=1;data=i;amount=j;tick();start=0;
      if(result !== i[7:0] || busy !== (j!=0) || done !== (j==0))$fatal(1,"Shift load");
      for(k=1;k<=j;k=k+1)begin
        // This hostile start and amount must be ignored while busy.
        start=1;data=8'hff;amount=7;tick();start=0;
        if(result !== (i>>k))$fatal(1,"Shift step");
        if(busy !== (k<j) || done !== (k==j))$fatal(1,"Shift completion");
        shift_checks=shift_checks+1;
      end
      saved=result;tick();
      if(result !== saved || busy !== 0 || done !== 0)$fatal(1,"Shift idle");
    end
    start=1;amount=7;data=8'hff;tick();start=0;rst=1;tick();rst=0;
    if(result !== 0 || busy !== 0 || done !== 0)$fatal(1,"Shift reset");
    // Exercise asynchronous reset while fclk is low, then sample #1 NBA behavior.
    #2;frst=0;#0.5;
    if(!$isunknown(fout))$fatal(1,"Unexpected initial output before reset update");
    #0.6;if(fout !== 1)$fatal(1,"Async source reset");frst=1;
    for(i=0;i<100;i=i+1)fib_tick((i%7)!=3);
    #2;frst=0;#1.1;if(fout !== 1)$fatal(1,"Repeated source reset");frst=1;fx=0;fy=1;
    fib_tick(0);fib_tick(1);
    // A pending delayed NBA is not canceled by a later asynchronous reset event.
    // fx=fy=1 after the last helper call; enabled data update precedes reset update.
    fen=1;#2;fclk=1;#0.2;frst=0;#0.85;
    if(fout !== 3)$fatal(1,"Pending NBA was unexpectedly canceled");
    #0.3;if(fout !== 1)$fatal(1,"Delayed reset did not follow pending NBA");fclk=0;
    $display("PASS pe=65536 compare=16 mean=258 shift_commands=2048 shift_steps=%0d fib_edges=%0d",shift_checks,fib_checks);
    $finish;
  end
endmodule

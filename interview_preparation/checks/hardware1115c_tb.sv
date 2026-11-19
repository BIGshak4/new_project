`timescale 1ns/1ps
module hardware1115c_tb;
  reg [6:0] x;
  wire [2:0] count;
  prep001_popcount7 bits7(x,count);
  reg clk,rst,entry_req,exit_req;
  wire [5:0] occupancy;
  wire full,accept_entry,accept_exit,reject_entry,reject_exit,state_error;
  prep356_parking park(clk,rst,entry_req,exit_req,occupancy,full,
                        accept_entry,accept_exit,reject_entry,reject_exit,state_error);
  integer value,index,expected,n,e,z,r,exit_ok,entry_ok,next_n,cases;
  initial begin
    x=0;clk=0;rst=0;entry_req=0;exit_req=0;cases=0;
    for(value=0;value<128;value=value+1) begin
      x=value;expected=0;
      for(index=0;index<7;index=index+1) expected=expected+((value>>index)&1);
      #1;
      if(count !== expected[2:0]) $fatal(1,"popcount x=%0d expected=%0d got=%0d",value,expected,count);
    end
    for(r=0;r<2;r=r+1)
      for(n=0;n<64;n=n+1)
        for(e=0;e<2;e=e+1)
          for(z=0;z<2;z=z+1) begin
            clk=0;park.occupancy=n;rst=r;entry_req=e;exit_req=z;
            exit_ok=0;entry_ok=0;
            if(r==0 && n<=50) begin
              if(z==1 && n>0) exit_ok=1;
              if(e==1 && (n<50 || exit_ok==1)) entry_ok=1;
            end
            next_n=n+entry_ok-exit_ok;
            if(r==1 || n>50) next_n=0;
            #1;
            if(accept_entry !== entry_ok[0] || accept_exit !== exit_ok[0])
              $fatal(1,"ack n=%0d e=%0d x=%0d rst=%0d",n,e,z,r);
            if(reject_entry !== (e[0] & ~entry_ok[0]) ||
               reject_exit !== (z[0] & ~exit_ok[0]))
              $fatal(1,"reject");
            if(full !== (n==50) || state_error !== (n>50))
              $fatal(1,"decode n=%0d",n);
            clk=1;#1;
            if(occupancy !== next_n[5:0])
              $fatal(1,"next n=%0d e=%0d x=%0d rst=%0d expected=%0d got=%0d",n,e,z,r,next_n,occupancy);
            cases=cases+1;
          end
    $display("PASS popcount=128 parking=512");
    $finish;
  end
endmodule

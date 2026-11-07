`timescale 1ns/1ps
module tb_hardware_1107n30;
  reg [9:0] x; wire [15:0] times49;
  reg [7:0] bits; wire [3:0] count;
  reg [3:0] a,b; wire [4:0] sum;
  reg ga,gb;wire nand_y;
  reg clk=0,rst=0,en=0;wire [3:0] phase;wire signed [15:0] sample;
  integer i,j,k,want,checks=0,expected_phase=0;
  integer sine[0:9];
  prep293_times49 m(x,times49);
  prep001_eight_fa_only p(bits,count);
  prep122_mixed s(a,b,sum);
  prep302_cmos_nand g(ga,gb,nand_y);
  prep299_sine_rom r(clk,rst,en,phase,sample);
  task tick;
    begin #1;clk=1;#1;clk=0;#1;end
  endtask
  initial begin
    x=0;bits=0;a=0;b=0;ga=0;gb=0;
    sine[0]=0;sine[1]=19260;sine[2]=31163;sine[3]=31163;sine[4]=19260;
    sine[5]=0;sine[6]=-19260;sine[7]=-31163;sine[8]=-31163;sine[9]=-19260;
    for(i=0;i<1024;i=i+1)begin
      x=i;#1;if(times49!==49*i)$fatal(1,"times49 %0d",i);checks=checks+1;
    end
    for(i=0;i<256;i=i+1)begin
      bits=i;want=0;for(j=0;j<8;j=j+1)want=want+((i>>j)&1);
      #1;if(count!==want)$fatal(1,"popcount %0d",i);checks=checks+1;
    end
    for(i=0;i<16;i=i+1)for(j=0;j<16;j=j+1)begin
      a=i;b=j;#1;if(sum!==(i+j))$fatal(1,"sum %0d %0d",i,j);checks=checks+1;
    end
    for(i=0;i<2;i=i+1)for(j=0;j<2;j=j+1)begin
      ga=i;gb=j;#1;if(nand_y!==!(i&j))$fatal(1,"NAND %0d %0d",i,j);checks=checks+1;
    end
    rst=1;en=1;tick();rst=0;
    if(phase!==0 || sample!==0)$fatal(1,"reset priority");checks=checks+1;
    for(k=0;k<123;k=k+1)begin
      en=(k%7!=0);rst=(k==41 || k==90);
      if(rst)expected_phase=0;
      else if(en)expected_phase=(expected_phase+1)%10;
      tick();
      if(phase!==expected_phase || sample!==sine[expected_phase])
        $fatal(1,"ROM phase %0d got %0d sample %0d",expected_phase,phase,sample);
      checks=checks+1;
    end
    $display("PASS hardware_1107n30 assertions=%0d times49=1024 popcount=256 adder_pairs=256 NAND_rows=4 sine_schedules=124",checks);
    $finish;
  end
endmodule

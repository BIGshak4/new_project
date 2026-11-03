`timescale 1ns/1ps
`include "prep_254_swap_five_seven.sv"
`include "prep_255_third_high_phase.sv"
`include "prep_256_room_balance.sv"
`include "prep_001_ha_three_batch1103.sv"
`include "prep_140_modular_squares_batch1103.sv"
`include "prep_152_load_extension_batch1103.sv"
module tb;
  integer checks=0;
  reg [2:0] x; wire [2:0] y;
  wire [1:0] pop; wire unused;
  prep254 swapper(x,y);
  prep001_ha3 popper(x,pop,unused);
  reg clk=0,rst=1,vin=0;
  wire out, gate_out; wire [1:0] count, gate_count;
  prep255 pulse(clk,rst,vin,out,count);
  prep255_gates gate_pulse(clk,rst,vin,gate_out,gate_count);
  reg room_clk=0,room_rst=1; reg [3:0] ev=0;
  wire red,green,blue; wire signed [4:0] diff;
  prep256 #(8) room(room_clk,room_rst,ev,red,green,blue,diff);
  reg sqclk=0,sqrst=1;
  wire [0:0] s1,o1; wire [3:0] s4,o4; wire [7:0] s8,o8;
  prep140_mod #(1) sq1(sqclk,sqrst,s1,o1);
  prep140_mod #(4) sq4(sqclk,sqrst,s4,o4);
  prep140_mod #(8) sq8(sqclk,sqrst,s8,o8);
  reg lclk=0,load=1;reg[4:0] data=0;wire[4:0] loaded;
  prep152_loaded ext(lclk,load,data,loaded);
  integer i,j,k,t,expected,runlen,men,women,eventn,nextmen,nextwomen,mask;
  task check(input condition);
    begin checks=checks+1; if(condition !== 1'b1) begin
      $display("FAIL check %0d at %0t",checks,$time); $fatal(1); end
    end
  endtask
  task room_edge;
    begin #2; room_clk=1; #2; room_clk=0; #2; end
  endtask
  task load_edge;
    begin #2; lclk=1; #2; lclk=0; #2; end
  endtask
  initial begin
    for(i=0;i<8;i=i+1) begin
      x=i;#2; expected=(i==5)?7:((i==7)?5:i);
      check(y==expected); check(pop==((i&1)+((i>>1)&1)+((i>>2)&1)));check(unused==0);
    end
    for(i=0;i<4096;i=i+1) begin
      rst=1;vin=0;clk=1;#3;clk=0;#3;rst=0;runlen=0;
      check(count==0);check(gate_count==0);
      for(j=0;j<12;j=j+1) begin
        vin=(i>>j)&1;#3;clk=1;#3;
        if(vin)runlen=runlen+1;else runlen=0;
        check(out==(runlen==3));check(gate_out==out);
        clk=0;#3;check(out==0);check(gate_out==0);
        expected=(runlen>3)?3:runlen;
        check(count==expected);check(gate_count==count);
      end
    end
    sqrst=1;#2;sqclk=1;#2;sqclk=0;#2;sqrst=0;
    for(i=1;i<=4096;i=i+1) begin
      sqclk=1;#2;
      check(s1==((i*i)&1));check(s4==((i*i)&15));check(s8==((i*i)&255));
      check(o1==((2*i+1)&1));check(o4==((2*i+1)&15));check(o8==((2*i+1)&255));
      sqclk=0;#2;
    end
    for(i=0;i<32;i=i+1)for(j=0;j<32;j=j+1)begin
      load=1;data=i;load_edge;check(loaded==i);
      load=0;data=j;load_edge;check(loaded==((i+1)&31));
      load=1;data=j;load_edge;check(loaded==j);
    end
    for(men=0;men<=8;men=men+1)for(women=0;women<=8-men;women=women+1)
      for(eventn=0;eventn<16;eventn=eventn+1)begin
        nextmen=men;nextwomen=women;
        if(eventn==8)nextmen=men-1;
        if(eventn==4)nextmen=men+1;
        if(eventn==2)nextwomen=women-1;
        if(eventn==1)nextwomen=women+1;
        if(nextmen>=0 && nextwomen>=0 && nextmen+nextwomen<=8)begin
          room_rst=1;ev=0;room_edge;room_rst=0;
          for(k=0;k<men;k=k+1)begin ev=4;room_edge;end
          for(k=0;k<women;k=k+1)begin ev=1;room_edge;end
          ev=eventn;room_edge;expected=nextmen-nextwomen;
          check($signed(diff)==expected);check(red==(expected>0));check(green==(expected==0));check(blue==(expected<0));
        end
      end
    $display("PASS batch1103 native hardware checks=%0d",checks);$finish;
  end
endmodule

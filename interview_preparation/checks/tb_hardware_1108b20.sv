`timescale 1ns/1ps
module tb_hardware_1108b20;
  reg [7:0] a,b;wire[7:0] hi,lo;
  reg clk=0,rst=0,en=0;reg[1:0] ab_short=0,ab_long=0;
  wire sr,sl,lr,ll;wire[4:0] phase;wire signed[15:0] sample;
  integer i,j,k,position,length_,direction,repeat_,expected_phase=0;
  integer checks=0,minmax_checks=0,wood_checks=0,sine_checks=0;
  integer table_[0:31];
  prep018_minmax8 m(a,b,hi,lo);
  prep053_wood_direction #(.SHORT_MODE(1)) ds(clk,rst,ab_short,sr,sl);
  prep053_wood_direction #(.SHORT_MODE(0)) dl(clk,rst,ab_long,lr,ll);
  prep299_sine32 s(clk,rst,en,phase,sample);
  task tick;begin #1;clk=1;#1;clk=0;#1;end endtask
  task passage(input integer short_mode,input integer to_right,input integer pauses);
    integer pos,len,step_,hold_,start_,finish_;reg[1:0] observation;
    reg want_r,want_l;
    begin
      len=short_mode ? 2 : 6;
      rst=1;ab_short=0;ab_long=0;tick();rst=0;
      start_=to_right ? -len-1 : 5;finish_=to_right ? 5 : -len-1;step_=to_right ? 1 : -1;
      pos=start_;
      while(pos!=finish_)begin
        pos=pos+step_;
        observation={1'(pos<=0 && pos+len>=0),1'(pos<=4 && pos+len>=4)};
        if(short_mode)ab_short=observation;else ab_long=observation;
        for(hold_=0;hold_<=pauses;hold_=hold_+1)begin
          want_r=to_right && pos==finish_ && hold_==0;
          want_l=!to_right && pos==finish_ && hold_==0;
          tick();
          if(short_mode)begin if(sr!==want_r || sl!==want_l)$fatal(1,"short passage");end
          else begin if(lr!==want_r || ll!==want_l)$fatal(1,"long passage");end
          wood_checks=wood_checks+1;
        end
      end
    end
  endtask
  initial begin
    a=0;b=0;
    table_[0]=0;table_[1]=6393;table_[2]=12539;table_[3]=18204;
    table_[4]=23170;table_[5]=27245;table_[6]=30273;table_[7]=32137;
    table_[8]=32767;table_[9]=32137;table_[10]=30273;table_[11]=27245;
    table_[12]=23170;table_[13]=18204;table_[14]=12539;table_[15]=6393;
    for(i=16;i<32;i=i+1)table_[i]=-table_[i-16];
    for(i=0;i<256;i=i+1)for(j=0;j<256;j=j+1)begin
      a=i;b=j;#1;
      if(hi!==(i>j?i:j) || lo!==(i<j?i:j))$fatal(1,"minmax");
      minmax_checks=minmax_checks+1;
    end
    for(i=0;i<2;i=i+1)for(j=0;j<2;j=j+1)for(k=0;k<4;k=k+1)passage(i,j,k);
    // Observable long-object reversal: enter, overlap, retreat, clear. No pulse.
    rst=1;ab_long=0;tick();rst=0;
    ab_long=2'b10;tick();if(lr||ll)$fatal(1,"long premature");
    ab_long=2'b11;tick();if(lr||ll)$fatal(1,"long premature");
    ab_long=2'b10;tick();if(lr||ll)$fatal(1,"long retreat");
    ab_long=2'b00;tick();if(lr||ll)$fatal(1,"long aborted");wood_checks=wood_checks+4;
    rst=1;en=1;tick();rst=0;expected_phase=0;
    if(phase!==0 || sample!==0)$fatal(1,"sine reset");sine_checks=sine_checks+1;
    for(k=0;k<193;k=k+1)begin
      rst=(k==61 || k==130);en=(k%9!=0);
      if(rst)expected_phase=0;else if(en)expected_phase=(expected_phase+1)%32;
      tick();
      if(phase!==expected_phase || sample!==table_[expected_phase])$fatal(1,"sine32");
      sine_checks=sine_checks+1;
    end
    checks=minmax_checks+wood_checks+sine_checks;
    $display("PASS hardware_1108b20 assertions=%0d minmax_pairs=%0d wood_samples=%0d sine_schedule=%0d",checks,minmax_checks,wood_checks,sine_checks);
    $finish;
  end
endmodule

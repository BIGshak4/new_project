`timescale 1ns/1ps
module tb_fifo;
  reg wclk=0,rclk=0,wrst_n=0,rrst_n=0;
  reg wen=0,ren=0;
  reg [7:0] wdata=0;
  wire [7:0] rdata;
  wire full,empty,rvalid;
  reg random_phase=0,drain=0;
  reg [31:0] ws=32'h12345678,rs=32'h87654321;
  reg [7:0] oracle[0:20000];
  integer head=0,tail=0,checks=0,reads=0,writes=0;
  reg take;
  reg [7:0] wanted;
  prep264 #(.AW(2),.W(8)) dut(wclk,wrst_n,wen,wdata,full,
                              rclk,rrst_n,ren,rdata,rvalid,empty);
  always #5 wclk=~wclk;
  always #7.5 rclk=~rclk; // no simultaneous rising edges with this write clock
  always @(negedge wclk) if(random_phase) begin
    ws<={ws[30:0],ws[31]^ws[21]^ws[1]^ws[0]};
    wen<=!drain && (ws[0] || ws[2]);wdata<=wdata+1;
  end
  always @(negedge rclk) if(random_phase) begin
    rs<={rs[30:0],rs[31]^rs[21]^rs[1]^rs[0]};
    ren<=drain || rs[0] || rs[3];
  end
  always @(posedge wclk) if(wrst_n && wen && !full) begin
    if(tail-head>=4) $fatal(1,"264 overflow before accepted write");
    oracle[tail]=wdata;tail=tail+1;writes=writes+1;checks=checks+1;
  end
  always @(posedge rclk) if(rrst_n) begin
    take=ren && !empty;
    if(take) begin
      if(head>=tail) $fatal(1,"264 underflow before accepted read");
      wanted=oracle[head];head=head+1;reads=reads+1;
    end
    #1;
    if(rvalid!==take) $fatal(1,"264 rvalid");
    if(take && rdata!==wanted) $fatal(1,"264 data mismatch");
    checks=checks+1;
  end
  initial begin
    // Hold reset through clocks; deassert far from local capture edges.
    #31;wrst_n=1;rrst_n=1;
    // One write at w45; first read capture R1=52.5, R2=67.5, R3=82.5.
    #10;wen=1;wdata=8'd91;
    #5;wen=0;ren=1;
    @(posedge rclk);#1;if(!empty || rvalid) $fatal(1,"264 R1 visibility");checks=checks+1;
    @(posedge rclk);#1;if(!empty || rvalid) $fatal(1,"264 R2 visibility");checks=checks+1;
    @(posedge rclk);#1;if(empty || rvalid) $fatal(1,"264 R3 empty flag");checks=checks+1;
    @(posedge rclk);#1;if(!empty || !rvalid || rdata!=91) $fatal(1,"264 R4 read");checks=checks+1;
    random_phase=1;
    #150000;
    drain=1;
    #2000;
    if(head!=tail || !empty) $fatal(1,"264 drain failed");
    if(reads<100 || writes<100) $fatal(1,"264 insufficient traffic");
    $display("PASS async FIFO checks=%0d accepted_writes=%0d accepted_reads=%0d",checks,writes,reads);
    $finish;
  end
  initial begin #160000;$fatal(1,"264 timeout");end
endmodule

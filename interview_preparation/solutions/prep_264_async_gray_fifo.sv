`timescale 1ns/1ps
// DEPTH=2**AW, AW>=1. Both domains must be reset together to flush safely.
// wrst_n/rrst_n assert asynchronously and must each deassert synchronously
// in their own clock domain. Memory is not reset. Read output is registered.
module prep264 #(parameter integer AW=2, W=8)
 (input wire wclk, wrst_n, w_en, input wire [W-1:0] w_data,
  output reg full,
  input wire rclk, rrst_n, r_en, output reg [W-1:0] r_data,
  output reg r_valid, empty);
  localparam integer DEPTH=(1<<AW);
  localparam [AW:0] FULL_MASK=(1<<AW)|(1<<(AW-1));
  reg [W-1:0] mem [0:DEPTH-1];
  reg [AW:0] wbin, wgray, rbin, rgray;
  (* async_reg = "true" *) reg [AW:0] wq1_rgray, wq2_rgray;
  (* async_reg = "true" *) reg [AW:0] rq1_wgray, rq2_wgray;
  wire wtake=w_en && !full;
  wire rtake=r_en && !empty;
  wire [AW:0] wnext=wbin+wtake;
  wire [AW:0] rnext=rbin+rtake;
  wire [AW:0] wg_next=(wnext>>1)^wnext;
  wire [AW:0] rg_next=(rnext>>1)^rnext;
  always @(posedge wclk or negedge wrst_n) begin
    if (!wrst_n) begin
      wbin<=0; wgray<=0; full<=0;
      wq1_rgray<=0; wq2_rgray<=0;
    end else begin
      wq1_rgray<=rgray; wq2_rgray<=wq1_rgray;
      if (wtake) mem[wbin[AW-1:0]]<=w_data;
      wbin<=wnext; wgray<=wg_next;
      full<=(wg_next==(wq2_rgray^FULL_MASK));
    end
  end
  always @(posedge rclk or negedge rrst_n) begin
    if (!rrst_n) begin
      rbin<=0; rgray<=0; empty<=1; r_valid<=0; r_data<=0;
      rq1_wgray<=0; rq2_wgray<=0;
    end else begin
      rq1_wgray<=wgray; rq2_wgray<=rq1_wgray;
      if (rtake) r_data<=mem[rbin[AW-1:0]];
      r_valid<=rtake;
      rbin<=rnext; rgray<=rg_next;
      empty<=(rg_next==rq2_wgray);
    end
  end
endmodule

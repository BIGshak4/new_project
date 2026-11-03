`timescale 1ns/1ps
// Explicit edited contract: Vin meets setup/hold at each falling edge.
// After two qualifying falling edges, emit only the following high phase.
module prep255(input wire clk, rst, vin, output wire out,
               output reg [1:0] count);
  always @(negedge clk) begin
    if (rst || !vin) count <= 2'd0;
    else if (count != 2'd3) count <= count + 2'd1;
  end
  assign out = !rst && clk && vin && (count == 2'd2);
endmodule

// Storage can be built from basic NAND gates, rather than assumed free.
module prep255_nand_latch(input wire d, en, output wire q);
  wire nd, sn, rn, qb;
  not(nd, d);
  nand(sn, d, en);
  nand(rn, nd, en);
  nand(q, sn, qb);
  nand(qb, rn, q);
endmodule

// Master transparent high, slave transparent low: falling-edge DFF.
module prep255_falling_ff_gates(input wire d, clk, output wire q);
  wire qm, nclk;
  not(nclk, clk);
  prep255_nand_latch master(d, clk, qm);
  prep255_nand_latch slave(qm, nclk, q);
endmodule

module prep255_gates(input wire clk, rst, vin, output wire out,
                     output wire [1:0] count);
  wire active, n0, n1, eq2;
  assign active = !rst && vin;
  assign n0 = active && (count[1] || !count[0]);
  assign n1 = active && (count[1] || count[0]);
  prep255_falling_ff_gates bit0(n0, clk, count[0]);
  prep255_falling_ff_gates bit1(n1, clk, count[1]);
  assign eq2 = count[1] && !count[0];
  assign out = !rst && clk && vin && eq2;
endmodule

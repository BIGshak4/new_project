module live_edge_polarities(input wire clk,d, output wire rise_only,fall_only,both_edges);
  reg q;
  // No source reset is specified. Observe outputs only after a known initial
  // d=0 sampling edge; initial X before that edge is intentionally retained.
  always @(posedge clk) q <= d;
  assign rise_only = d & ~q;
  assign fall_only = q & ~d;
  assign both_edges = d ^ q;
endmodule

// Behavioral ideal edge-triggered active-high SR primitive.
// Do not replace this with an unclocked SR latch and claim a DFF.
module srff_ideal(input logic clk, s, r, output logic q);
  always_ff @(posedge clk) begin
    case ({s,r})
      2'b00: q <= q;
      2'b01: q <= 1'b0;
      2'b10: q <= 1'b1;
      default: q <= 1'bx; // forbidden 11; simulation diagnostic only
    endcase
  end
endmodule

module dff_from_sr(input logic clk, d, output logic q);
  wire s = d;
  wire r = ~d;
  srff_ideal storage(.clk(clk), .s(s), .r(r), .q(q));
endmodule

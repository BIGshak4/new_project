// Conceptual RTL only: not compiled, synthesized, timed or approved for silicon.
// A library DFF/always_ff should normally implement an edge register; a raw MUX
// feedback loop is not a portable physical storage primitive.
module prep_083_d_latch(input logic d, en, output logic q);
    always_latch begin
        if (en) q <= d;
    end
endmodule

module prep_083_master_slave(input logic d, clk, output wire q);
    wire m;
    prep_083_d_latch master(.d(d), .en(~clk), .q(m));
    prep_083_d_latch slave (.d(m), .en(clk),  .q(q));
endmodule

module prep_083_enabled_register #(parameter int W = 8)
    (input logic clk, en, input logic [W-1:0] d, output logic [W-1:0] q);
    // This describes a MUX before each DFF, rather than a gated clock.
    always_ff @(posedge clk) begin
        if (en) q <= d;
    end
endmodule

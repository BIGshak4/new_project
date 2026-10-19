// Behavioral definition of the supplied A primitive, not a physical-cell claim.
module threshold_a (
    input  logic a, b, c, d,
    output logic y
);
    assign y = (a & b) | (a & c) | (a & d)
             | (b & c) | (b & d) | (c & d);
endmodule

// Four A instances. Only direct wires and free binary constants are added.
module threshold_three_of_four (
    input  logic a, b, c, d,
    output logic y
);
    logic p, q, r;
    threshold_a g1 (.a(c), .b(d), .c(1'b0), .d(1'b0), .y(p));
    threshold_a g2 (.a(c), .b(d), .c(1'b1), .d(1'b0), .y(q));
    threshold_a g3 (.a(a), .b(b), .c(p), .d(1'b0), .y(r));
    threshold_a g4 (.a(r), .b(q), .c(1'b0), .d(1'b0), .y(y));
endmodule

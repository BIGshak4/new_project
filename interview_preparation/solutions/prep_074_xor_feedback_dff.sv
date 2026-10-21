// Behavioral illustration only: not compiled, synthesized or HDL-simulated.
module xor_feedback_dff (
    input logic clk, input logic a, output logic q
);
    // No reset was specified. q may be unknown until initialized externally.
    // A=0 holds even unknown q; A=1 does not resolve an unknown initial q.
    always_ff @(posedge clk) q <= q ^ a;
endmodule

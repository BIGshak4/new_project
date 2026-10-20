// Only mux selections and constant zero; no constant one or inversion.
// A ternary expression below denotes one 2:1 MUX, not a generic gate.
// No HDL compilation, simulation or synthesis was performed for this file.
module xor_three_mux_zero (
    input logic A, B, C,
    output logic F
);
    logic t, P, u;
    assign t = B ? 1'b0 : A;
    assign P = A ? t : B;
    assign u = C ? 1'b0 : P;
    assign F = P ? u : C;
endmodule

// Five explicit 2:1 mux selections, constants 0/1, no external inversion.
// Functionally checked using a matching Python mux netlist, not HDL simulation.
module full_adder_mux (
    input logic A, B, Cin,
    output logic S, Cout
);
    logic nB, P, nCin;
    assign nB = B ? 1'b0 : 1'b1;
    assign P = A ? nB : B;
    assign nCin = Cin ? 1'b0 : 1'b1;
    assign S = P ? nCin : Cin;
    assign Cout = P ? Cin : A;
endmodule

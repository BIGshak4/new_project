// PREP-058: N>=2; unsigned inputs, exact integer relation b=a+2, no wrap.
// No arithmetic operators in the hardware datapath. Index/range expressions
// are elaboration constants, not adders in the circuit.
module average_difference_two #(parameter int N = 8) (
    input  logic [N-1:0] a,
    input  logic [N-1:0] b,
    output logic [N-1:0] y
);
    assign y[0] = ~a[0];
    assign y[N-1:1] = ({(N-1){~a[0]}} & a[N-1:1])
                    | ({(N-1){ a[0]}} & b[N-1:1]);
endmodule

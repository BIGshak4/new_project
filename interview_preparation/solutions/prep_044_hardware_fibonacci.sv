// W >= 1. Synchronous reset; output after k nonreset edges is F_k mod 2**W.
module hardware_fibonacci #(
    parameter int unsigned W = 16
) (
    input  logic         clk,
    input  logic         rst,
    output logic [W-1:0] value
);
    logic [W-1:0] a, b;

    assign value = a;

    always_ff @(posedge clk) begin
        if (rst) begin
            a <= '0;
            b <= 1;
        end else begin
            a <= b;
            b <= a + b;
        end
    end
endmodule

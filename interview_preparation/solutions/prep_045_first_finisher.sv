// Finish pulses must already meet this clock domain's setup/hold requirements.
// Simultaneous sampled pulses use explicit editorial priority: lane 1 > 2 > 3.
module first_finisher (
    input  logic       clk,
    input  logic       REST,
    input  logic       p1,
    input  logic       p2,
    input  logic       p3,
    output logic [1:0] winner
);
    logic [1:0] candidate;
    logic       en;

    // One-bit NOR result, not a bitwise inversion of the two-bit winner.
    assign en = ~(winner[1] | winner[0]);

    always_comb begin
        if      (p1) candidate = 2'b01;
        else if (p2) candidate = 2'b10;
        else if (p3) candidate = 2'b11;
        else         candidate = 2'b00;
    end

    always_ff @(posedge clk) begin
        if (REST)
            winner <= 2'b00;
        else if (en)
            winner <= candidate;
        // Reset overrides enable, including when en=0 after a win.
        // Otherwise hold winner; later pulses cannot replace it.
    end
endmodule

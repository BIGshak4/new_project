// Finish pulses must already meet this clock domain's setup/hold requirements.
// Simultaneous sampled pulses use explicit editorial priority: lane 1 > 2 > 3.
module first_finisher (
    input  logic       clk,
    input  logic       rst,
    input  logic       p1,
    input  logic       p2,
    input  logic       p3,
    output logic [1:0] winner
);
    logic [1:0] candidate;

    always_comb begin
        if      (p1) candidate = 2'b01;
        else if (p2) candidate = 2'b10;
        else if (p3) candidate = 2'b11;
        else         candidate = 2'b00;
    end

    always_ff @(posedge clk) begin
        if (rst)
            winner <= 2'b00;
        else if (winner == 2'b00)
            winner <= candidate;
        // Otherwise hold winner; later pulses cannot replace it.
    end
endmodule

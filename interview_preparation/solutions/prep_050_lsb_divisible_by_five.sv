// Proposed five-state Moore FSM. Empty word represents zero.
// Observe divisible after the last accepted bit's rising edge.
// This file has not been compiled or HDL-simulated in this preparation run.
module lsb_divisible_by_five (
    input  logic clk,
    input  logic rst,
    input  logic bit_valid,
    input  logic bit_in,
    output logic divisible
);
    logic [2:0] state, next_state;

    always_comb begin
        case (state)
            3'd0: next_state = bit_in ? 3'd3 : 3'd0;
            3'd1: next_state = bit_in ? 3'd1 : 3'd3;
            3'd2: next_state = bit_in ? 3'd4 : 3'd1;
            3'd3: next_state = bit_in ? 3'd2 : 3'd4;
            3'd4: next_state = bit_in ? 3'd0 : 3'd2;
            default: next_state = 3'd0;  // defensive unused-code recovery
        endcase
    end

    always_ff @(posedge clk) begin
        if (rst)
            state <= 3'd0;
        else if (bit_valid)
            state <= next_state;
    end

    assign divisible = (state == 3'd0);
endmodule

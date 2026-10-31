// Proposed Moore RTL; synchronous reset; overlapping detections after sampling.
module sequence_1101 (
    input logic clk, rst, bit_in,
    output logic found
);
    logic [2:0] state, next_state;
    always_comb begin
        case (state)
            3'd0: next_state = bit_in ? 3'd1 : 3'd0;
            3'd1: next_state = bit_in ? 3'd2 : 3'd0;
            3'd2: next_state = bit_in ? 3'd2 : 3'd3;
            3'd3: next_state = bit_in ? 3'd4 : 3'd0;
            3'd4: next_state = bit_in ? 3'd2 : 3'd0;
            default: next_state = 3'd0;
        endcase
    end
    always_ff @(posedge clk) begin
        if (rst) state <= 3'd0;
        else state <= next_state;
    end
    assign found = state == 3'd4;
endmodule

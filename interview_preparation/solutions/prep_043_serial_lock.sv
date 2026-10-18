module abcd_detector (
    input  logic       clk,
    input  logic       rst,
    input  logic [7:0] symbol,
    output logic       detected
);
    typedef enum logic [1:0] { S0, S1, S2, S3 } state_t;
    state_t state, next_state;
    logic next_detected;

    always_comb begin
        next_state = S0;
        next_detected = 1'b0;
        case (state)
            S0: if (symbol == 8'h41) next_state = S1;
            S1: begin
                if (symbol == 8'h41) next_state = S1;
                else if (symbol == 8'h42) next_state = S2;
            end
            S2: begin
                if (symbol == 8'h41) next_state = S1;
                else if (symbol == 8'h43) next_state = S3;
            end
            S3: begin
                if (symbol == 8'h41) next_state = S1;
                else if (symbol == 8'h44) next_detected = 1'b1;
            end
            default: begin
                next_state = S0;
                next_detected = 1'b0;
            end
        endcase
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= S0;
            detected <= 1'b0;
        end else begin
            state <= next_state;
            detected <= next_detected;
        end
    end
endmodule

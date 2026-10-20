// PREP-053. a,b are already synchronized, debounced and sampled slowly enough
// to preserve ALL overlap transitions. Raw asynchronous sensors need a front end.
// rst is synchronous; assert only with AB=00 and known initial occupancy=0.
module doorway_counter #(parameter int W = 8) (
    input logic clk, rst, a, b,
    output logic [W-1:0] count,
    output logic count_valid,
    output logic entry_pulse, exit_pulse
);
    typedef enum logic [2:0] {IDLE,E1,E2,E3,X1,X2,X3,WAIT_CLEAR} state_t;
    state_t state, next_state;
    logic enter, leave, bad;

    always_comb begin
        next_state = WAIT_CLEAR;
        case (state)
            IDLE: case ({a,b})
                2'b00: next_state=IDLE; 2'b10: next_state=E1;
                2'b01: next_state=X1; default: next_state=WAIT_CLEAR;
            endcase
            E1: case ({a,b})
                2'b00: next_state=IDLE; 2'b10: next_state=E1;
                2'b11: next_state=E2; default: next_state=WAIT_CLEAR;
            endcase
            E2: case ({a,b})
                2'b10: next_state=E1; 2'b11: next_state=E2;
                2'b01: next_state=E3; default: next_state=WAIT_CLEAR;
            endcase
            E3: case ({a,b})
                2'b00: next_state=IDLE; 2'b01: next_state=E3;
                2'b11: next_state=E2; default: next_state=WAIT_CLEAR;
            endcase
            X1: case ({a,b})
                2'b00: next_state=IDLE; 2'b01: next_state=X1;
                2'b11: next_state=X2; default: next_state=WAIT_CLEAR;
            endcase
            X2: case ({a,b})
                2'b01: next_state=X1; 2'b11: next_state=X2;
                2'b10: next_state=X3; default: next_state=WAIT_CLEAR;
            endcase
            X3: case ({a,b})
                2'b00: next_state=IDLE; 2'b10: next_state=X3;
                2'b11: next_state=X2; default: next_state=WAIT_CLEAR;
            endcase
            WAIT_CLEAR: if ({a,b}==2'b00) next_state=IDLE;
            default: next_state=WAIT_CLEAR;
        endcase
        enter = state==E3 && {a,b}==2'b00;
        leave = state==X3 && {a,b}==2'b00;
        bad = next_state==WAIT_CLEAR && state!=WAIT_CLEAR;
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            count <= '0;
            count_valid <= 1'b1;
            entry_pulse <= 1'b0;
            exit_pulse <= 1'b0;
        end else begin
            state <= next_state;
            entry_pulse <= 1'b0;
            exit_pulse <= 1'b0;
            if (bad) count_valid <= 1'b0;
            if (enter) begin
                if (&count) count_valid <= 1'b0;
                else begin count <= count + 1'b1; entry_pulse <= 1'b1; end
            end else if (leave) begin
                if (count=='0) count_valid <= 1'b0;
                else begin count <= count - 1'b1; exit_pulse <= 1'b1; end
            end
        end
    end
endmodule

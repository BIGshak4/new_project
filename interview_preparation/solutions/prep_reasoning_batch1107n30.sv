// Synthesizable finite-state designs. The separate router driver is test code.
module prep292_counter0121(input logic clk, rst,
                          output logic [1:0] value);
    logic [1:0] phase;
    always_ff @(posedge clk) begin
        if (rst) phase <= 2'b00;
        else phase <= phase + 2'b01;
    end
    assign value = {phase[1] & ~phase[0], phase[0]};
endmodule

module prep301_room(input logic clk, rst,
                    input logic [1:0] event_code,
                    output logic lamp, rejected,
                    output logic [1:0] occupancy);
    // 00idle,01entry,10exit,11invalid. Rejected is combinational pre-edge status.
    always_comb begin
        rejected = (event_code == 2'b11) ||
                   ((event_code == 2'b01) && (occupancy == 2'd3)) ||
                   ((event_code == 2'b10) && (occupancy == 2'd0));
    end
    always_ff @(posedge clk) begin
        if (rst) occupancy <= 2'd0;
        else if (!rejected) begin
            case (event_code)
                2'b01: occupancy <= occupancy + 2'd1;
                2'b10: occupancy <= occupancy - 2'd1;
                default: occupancy <= occupancy;
            endcase
        end
    end
    assign lamp = |occupancy;
endmodule

module prep036_left_div3_lag(input logic clk, rst, bit_in,
                            output logic divisible);
    logic [1:0] state;
    logic seen;
    // state = prefix * 2^(-accepted_length) mod3. Two binary bits encode3states.
    always_ff @(posedge clk) begin
        if (rst) begin state <= 2'd0; seen <= 1'b0; divisible <= 1'b0; end
        else begin
            divisible <= seen && (state == 2'd0);
            seen <= 1'b1;
            case (state)
                2'd0: state <= bit_in ? 2'd2 : 2'd0;
                2'd1: state <= bit_in ? 2'd1 : 2'd2;
                2'd2: state <= bit_in ? 2'd0 : 2'd1;
                default: begin state <= 2'd0; seen <= 1'b0; divisible <= 1'b0; end
            endcase
        end
    end
endmodule

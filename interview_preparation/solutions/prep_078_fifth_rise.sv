// Source input x is synchronous to clk and satisfies setup/hold.
// rst is synchronous active high; a required reset edge clears history.
module every_fifth_rise (
    input  logic clk, rst, x,
    output logic pulse,
    output logic [2:0] count
);
    logic previous;
    wire event_rise = x & ~previous;

    always_ff @(posedge clk) begin
        if (rst) begin
            previous <= 1'b0;
            count <= 3'd0;
            pulse <= 1'b0;
        end else begin
            previous <= x;
            pulse <= event_rise && (count == 3'd4);
            if (event_rise)
                count <= (count == 3'd4) ? 3'd0 : count + 3'd1;
        end
    end
endmodule

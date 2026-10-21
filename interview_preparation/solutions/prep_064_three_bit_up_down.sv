// Three same-clock DFFs, gates only. No FA/HA, +, -, gated clock or ripple clock.
// inc/dec are synchronous bits meeting setup/hold; rst is synchronous active high.
// The result wraps modulo eight. No HDL compilation/simulation is claimed.
module three_bit_up_down (
    input  logic clk, rst, inc, dec,
    output logic [2:0] q
);
    logic up, down;
    logic [2:0] toggle, d;

    assign up = inc & ~dec;
    assign down = dec & ~inc;
    assign toggle[0] = up | down;
    assign toggle[1] = (up & q[0]) | (down & ~q[0]);
    assign toggle[2] = (up & q[1] & q[0]) | (down & ~q[1] & ~q[0]);
    assign d = q ^ toggle;

    always_ff @(posedge clk) begin
        if (rst)
            q <= 3'b000;
        else
            q <= d;
    end
endmodule

module rising_edge_detector (
    input  logic clk,
    input  logic rst,
    input  logic x,
    output logic pulse
);
    logic previous;

    always_ff @(posedge clk) begin
        if (rst) begin
            previous <= 1'b0;
            pulse    <= 1'b0;
        end else begin
            pulse    <= x & ~previous;
            previous <= x;
        end
    end
endmodule

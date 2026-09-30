// Divide by three, 50% output duty for a 50% duty input clock.
// Ideal logic model; reset release must meet recovery/removal at both edges.
module divide_by_three (
    input  logic clk,
    input  logic rst_n,
    output wire  clk_div3
);
    logic q1, q0, delayed;
    wire q1_n = ~q1;
    wire q0_n = ~q0;
    // In the schematic q1_n/q0_n are complementary FF output pins.
    // RTL describes the Boolean function; technology mapping selects cells.

    // (q1,q0): 00 -> 10 -> 01 -> 00. Illegal 11 recovers to 01.
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q1 <= 1'b0;
            q0 <= 1'b0;
        end else begin
            q1 <= q1_n & q0_n;
            q0 <= q1;
        end
    end

    always_ff @(negedge clk or negedge rst_n) begin
        if (!rst_n)
            delayed <= 1'b0;
        else
            delayed <= q1;
    end

    assign clk_div3 = q1 | delayed;
endmodule

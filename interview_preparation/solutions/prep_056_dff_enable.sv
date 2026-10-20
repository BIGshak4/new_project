// PREP-056: one ordinary DFF with feedback mux. No reset was requested.
// en and data are synchronous signals meeting setup/hold around posedge clk.
module dff_with_enable (
    input  logic clk,
    input  logic data,
    input  logic en,
    output logic q
);
    logic d_next;
    assign d_next = (en & data) | (~en & q);

    always_ff @(posedge clk)
        q <= d_next;
endmodule

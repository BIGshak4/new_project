// Pulse high after input edges 3, 6, 9, ... since the last reset edge.
module every_third_clock (
    input  logic clk,
    input  logic rst,
    output logic pulse
);
    logic [1:0] count;

    always_ff @(posedge clk) begin
        if (rst) begin
            count <= 2'd0;
            pulse <= 1'b0;
        end else if (count == 2'd2) begin
            count <= 2'd0;
            pulse <= 1'b1;
        end else begin
            count <= count + 2'd1;
            pulse <= 1'b0;
        end
    end
endmodule

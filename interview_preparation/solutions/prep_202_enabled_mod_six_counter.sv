// Proposed RTL; Python transition model was executed. HDL not compiled here.
module enabled_mod_six_counter (
    input logic clk, rst, enable,
    output logic [2:0] count
);
    always_ff @(posedge clk) begin
        if (rst) count <= 3'd0;
        else if (count >= 3'd6) count <= 3'd0;
        else if (enable) count <= count == 3'd5 ? 3'd0 : count + 3'd1;
    end
endmodule

// Proposed synchronous RTL. Verified with a Python model, not compiled here.
module floor_log2_counter (
    input logic clk, rst, start,
    input logic [15:0] x,
    output logic [3:0] result,
    output logic busy, done, valid
);
    logic [15:0] work;
    logic [3:0] count;
    always_ff @(posedge clk) begin
        if (rst) begin
            work <= '0;
            count <= '0;
            result <= '0;
            busy <= 1'b0;
            done <= 1'b0;
            valid <= 1'b0;
        end else begin
            done <= 1'b0;
            if (busy) begin
                if (work > 16'd1) begin
                    work <= work >> 1;
                    count <= count + 4'd1;
                end else begin
                    result <= count;
                    busy <= 1'b0;
                    done <= 1'b1;
                    valid <= 1'b1;
                end
            end else if (start) begin
                work <= x;
                count <= '0;
                valid <= 1'b0;
                if (x == 16'd0) begin
                    result <= '0;
                    done <= 1'b1;
                end else begin
                    busy <= 1'b1;
                end
            end
        end
    end
endmodule

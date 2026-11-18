module square_equality_from_recurrence #(
    parameter integer N = 4
) (
    input wire clk, rst,
    input wire [N-1:0] a, b, c,
    output reg equal, valid
);
    reg started;
    reg [N-1:0] target_a, target_b, target_c, terminal_index, idx;
    reg [2*N-1:0] square, saved_a, saved_b, saved_c;
    wire [N-1:0] max_ab = a >= b ? a : b;
    wire [N-1:0] maximum = max_ab >= c ? max_ab : c;
    wire [N-1:0] next_idx = idx + 1'b1;
    wire [2*N-1:0] odd_step = {idx, 1'b1};
    wire [2*N-1:0] next_square = square + odd_step;
    wire [2*N-1:0] out_a = next_idx == target_a ? next_square : saved_a;
    wire [2*N-1:0] out_b = next_idx == target_b ? next_square : saved_b;
    wire [2*N-1:0] out_c = next_idx == target_c ? next_square : saved_c;
    wire [2*N:0] sum_ab = {1'b0, out_a} + {1'b0, out_b};

    always @(posedge clk) begin
        if (rst) begin
            started <= 0;
            target_a <= 0;
            target_b <= 0;
            target_c <= 0;
            terminal_index <= 0;
            idx <= 0;
            square <= 0;
            saved_a <= 0;
            saved_b <= 0;
            saved_c <= 0;
            equal <= 0;
            valid <= 0;
        end else if (!started) begin
            started <= 1;
            target_a <= a;
            target_b <= b;
            target_c <= c;
            terminal_index <= maximum;
            if (maximum == 0) begin
                equal <= 1;
                valid <= 1;
            end
        end else if (!valid) begin
            idx <= next_idx;
            square <= next_square;
            saved_a <= out_a;
            saved_b <= out_b;
            saved_c <= out_c;
            if (next_idx == terminal_index) begin
                equal <= (sum_ab == {1'b0, out_c});
                valid <= 1;
            end
        end
    end
endmodule

module count_byte_7e #(
    parameter integer WIDTH = 4
) (
    input wire clk, rst, in_valid,
    input wire [7:0] data,
    output reg [WIDTH-1:0] count,
    output reg overflow
);
    wire match_byte = (data == 8'h7e);
    always @(posedge clk) begin
        if (rst) begin
            count <= 0;
            overflow <= 0;
        end else if (in_valid && match_byte) begin
            if (&count)
                overflow <= 1;
            else
                count <= count + 1'b1;
        end
    end
endmodule

module report_dissent (
    input wire a, b, c,
    output wire disagree,
    output wire [2:0] odd_one_hot
);
    wire ab = a ^ b;
    wire ac = a ^ c;
    wire bc = ab ^ ac;
    assign disagree = ab | ac;
    assign odd_one_hot = {ab & ac, ab & bc, ac & bc};
endmodule

module p_cell (input wire a, b, output wire y);
    assign y = (!a && !b) ? 1'b1 : 1'bz;
endmodule

module n_cell (input wire a, b, output wire y);
    assign y = (a && b) ? 1'b0 : 1'bz;
endmodule

module p_n_gates (input wire a, b, output wire inv_a, nor_ab);
    p_cell inv_p(a, a, inv_a);
    n_cell inv_n(a, a, inv_a);
    p_cell nor_p(a, b, nor_ab);
    n_cell nor_n_a(a, a, nor_ab);
    n_cell nor_n_b(b, b, nor_ab);
endmodule

module nand_six (input wire a, b, output wire buf_a, not_a, and_ab, or_ab, nor_ab, xor_ab);
    wire not_b, ab_neg, p, q;
    nand (not_a, a, a);
    nand (not_b, b, b);
    nand (buf_a, not_a, not_a);
    nand (ab_neg, a, b);
    nand (and_ab, ab_neg, ab_neg);
    nand (or_ab, not_a, not_b);
    nand (nor_ab, or_ab, or_ab);
    nand (p, a, ab_neg);
    nand (q, b, ab_neg);
    nand (xor_ab, p, q);
endmodule

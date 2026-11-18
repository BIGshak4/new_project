`timescale 1ns/1ps

module digital1118_tb;
    reg clk = 0;
    always #5 clk = ~clk;

    reg square_reset = 1;
    reg [3:0] a = 0, b = 0, c = 0;
    wire equal, square_valid;
    square_equality_from_recurrence #(.N(4)) squares(clk, square_reset, a, b, c, equal, square_valid);
    wire equal_n1, square_valid_n1;
    square_equality_from_recurrence #(.N(1)) squares_n1(
        clk, square_reset, a[0], b[0], c[0], equal_n1, square_valid_n1
    );

    reg count_reset = 1, in_valid = 0;
    reg [7:0] data = 0;
    wire [1:0] count;
    wire count_n1, overflow, overflow_n1;
    count_byte_7e #(.WIDTH(2)) bytes(clk, count_reset, in_valid, data, count, overflow);
    count_byte_7e #(.WIDTH(1)) bytes_n1(clk, count_reset, in_valid, data, count_n1, overflow_n1);

    reg ca = 0, cb = 0, cc = 0;
    wire disagree, p_inv, p_nor, g_buf, g_not, g_and, g_or, g_nor, g_xor;
    wire [2:0] odd;
    report_dissent observer_core(ca, cb, cc, disagree, odd);
    p_n_gates tri_state(ca, cb, p_inv, p_nor);
    nand_six all_gates(ca, cb, g_buf, g_not, g_and, g_or, g_nor, g_xor);

    integer cases_square = 0, edges_square = 0, cases_byte = 0, cases_logic = 0;
    integer given_a, given_b, given_c, cycle, terminal_cycle, expected_matches = 0, i;

    task capture_edge;
        begin
            @(posedge clk);
            #1;
        end
    endtask

    task count_one_sample(input bit reset_value, input bit valid_value, input logic [7:0] word_value);
        begin
            @(negedge clk);
            count_reset = reset_value;
            in_valid = valid_value;
            data = word_value;
            if (reset_value)
                expected_matches = 0;
            else if (valid_value && word_value == 8'h7e)
                expected_matches = expected_matches + 1;
            capture_edge;
            if (count !== (expected_matches > 3 ? 2'd3 : expected_matches[1:0]) ||
                overflow !== (expected_matches > 3) ||
                count_n1 !== (expected_matches > 0) ||
                overflow_n1 !== (expected_matches > 1))
                $fatal(1, "byte value=%02x valid=%d matched=%d", word_value, valid_value, expected_matches);
            cases_byte = cases_byte + 1;
        end
    endtask

    initial begin
        for (i = 0; i < 8; i = i + 1) begin
            {ca, cb, cc} = i[2:0];
            #1;
            if (disagree !== !(ca == cb && cb == cc) ||
                odd !== {(cb == cc && ca != cb), (ca == cc && cb != ca), (ca == cb && cc != ca)} ||
                p_inv !== !ca || p_nor !== !(ca || cb) ||
                {g_buf,g_not,g_and,g_or,g_nor,g_xor} !== {ca,!ca,(ca && cb),(ca || cb),!(ca || cb),(ca != cb)})
                $fatal(1, "combinational result mismatch for %03b", i[2:0]);
            cases_logic = cases_logic + 1;
        end
        for (i = 0; i < 256; i = i + 1) begin
            count_one_sample(1, 1, 8'h7e);
            count_one_sample(0, 1, i[7:0]);
        end
        for (i = 0; i < 6; i = i + 1) begin
            count_one_sample(0, 0, 8'h7e);
            count_one_sample(0, 1, 8'h7e);
        end
        count_one_sample(0, 1, 8'h7f);
        count_one_sample(1, 1, 8'h7e);

        for (given_a = 0; given_a < 16; given_a = given_a + 1)
            for (given_b = 0; given_b < 16; given_b = given_b + 1)
                for (given_c = 0; given_c < 16; given_c = given_c + 1) begin
                    terminal_cycle = given_a >= given_b ? given_a : given_b;
                    if (given_c > terminal_cycle) terminal_cycle = given_c;
                    @(negedge clk);
                    square_reset = 1;
                    capture_edge;
                    if ({square_valid, equal, square_valid_n1, equal_n1} !== 4'b0000)
                        $fatal(1, "square reset priority");
                    @(negedge clk);
                    square_reset = 0;
                    a = given_a[3:0];
                    b = given_b[3:0];
                    c = given_c[3:0];
                    capture_edge;
                    if (square_valid !== (terminal_cycle == 0)) $fatal(1, "square capture valid");
                    if (square_valid_n1 !== !(given_a[0] || given_b[0] || given_c[0]))
                        $fatal(1, "square N=1 capture valid");
                    for (cycle = 1; cycle <= terminal_cycle+1; cycle = cycle + 1) begin
                        @(negedge clk);
                        // The checker must ignore the bus after capturing operands.
                        a = ~given_a[3:0];
                        b = ~given_b[3:0];
                        c = ~given_c[3:0];
                        capture_edge;
                        if (square_valid !== (cycle >= terminal_cycle)) $fatal(1, "square latency");
                        if (!square_valid_n1 || equal_n1 !==
                            (int'(given_a[0]) + int'(given_b[0]) == int'(given_c[0])))
                            $fatal(1, "square N=1 result");
                        if (square_valid && equal !== (given_a*given_a + given_b*given_b == given_c*given_c))
                            $fatal(1, "square result for %d %d %d", given_a, given_b, given_c);
                        edges_square = edges_square + 1;
                    end
                    cases_square = cases_square + 1;
                end
        $display("PASS square_cases=%0d square_observation_edges=%0d count_samples=%0d logic_vectors=%0d",
                 cases_square, edges_square, cases_byte, cases_logic);
        $finish;
    end
endmodule

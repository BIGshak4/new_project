// Procedural simulation driver, not synthesizable RTL or constrained-random SV.
// send_data below is the test spy. Replace its body with the supplied synchronous
// interface in an actual environment, preserving the scoreboard independently.
module prep291_router_driver;
    integer ports[0:15];
    integer budgets[0:15];
    integer hits[0:15];
    integer total_sent, packet_count;
    reg [31:0] random_state;

    function automatic integer pick(input integer upper_exclusive);
        reg [31:0] x;
        begin
            if (upper_exclusive <= 0) $fatal(1, "invalid random range");
            x = random_state;
            x = x ^ (x << 13); x = x ^ (x >> 17); x = x ^ (x << 5);
            random_state = x;
            // Bounded modulo selection is reproducible, not exactly uniform.
            pick = x % upper_exclusive;
        end
    endfunction

    task automatic send_data(input integer port_num, input integer data_size);
        begin
            if (port_num < 0 || port_num > 15 || data_size < 2 || data_size > 65536)
                $fatal(1, "illegal packet");
            hits[port_num] = hits[port_num] + 1;
            total_sent = total_sent + data_size;
            packet_count = packet_count + 1;
        end
    endtask

    task automatic run_test(input integer total, input integer active_count,
                            input reg [31:0] seed);
        integer i, j, swap_port, remaining, extra, take, upper, skip, count, size;
        reg skip_present;
        begin
            if (active_count < 1 || active_count > 16 || total < 2*active_count || total > 1000000)
                $fatal(1, "infeasible configuration");
            random_state = seed == 0 ? 32'h1 : seed;
            total_sent = 0; packet_count = 0;
            for (i = 0; i < 16; i = i+1) begin ports[i] = i; hits[i] = 0; end
            for (i = 15; i > 0; i = i-1) begin
                j = pick(i+1); swap_port = ports[i]; ports[i] = ports[j]; ports[j] = swap_port;
            end
            extra = total - 2*active_count;
            for (i = 0; i < active_count; i = i+1) begin
                take = i == active_count-1 ? extra : pick(extra+1);
                budgets[i] = 2 + take; extra = extra-take;
            end
            for (i = 0; i < active_count; i = i+1) begin
                remaining = budgets[i];
                while (remaining != 0) begin
                    upper = remaining < 65536 ? remaining : 65536;
                    skip = remaining-1;
                    skip_present = skip >= 2 && skip <= upper;
                    count = upper-1-(skip_present ? 1 : 0);
                    size = 2+pick(count);
                    if (skip_present && size >= skip) size = size+1;
                    send_data(ports[i], size);
                    remaining = remaining-size;
                end
            end
            if (total_sent != total) $fatal(1, "byte conservation failed");
            for (i = 0; i < 16; i = i+1) begin
                if (i < active_count && hits[ports[i]] == 0) $fatal(1, "active port omitted");
                if (i >= active_count && hits[ports[i]] != 0) $fatal(1, "inactive port used");
            end
        end
    endtask

    task automatic random_test(input integer max_total, input reg [31:0] seed);
        integer p, total, max_ports;
        reg [31:0] next_seed;
        begin
            if (max_total < 2 || max_total > 1000000) $fatal(1, "invalid test maximum");
            random_state = seed == 0 ? 32'h1 : seed;
            max_ports = max_total/2 < 16 ? max_total/2 : 16;
            p = 1+pick(max_ports);
            total = 2*p+pick(max_total-2*p+1);
            next_seed = random_state;
            run_test(total, p, next_seed);
        end
    endtask
endmodule

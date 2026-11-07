`timescale 1ns/1ps
// Educational W-bit sequential predicate. W >= 2; unsigned inputs.
// start is accepted only while !busy. valid pulses on completion.
// rst is synchronous and overrides a simultaneous request.
module prep_265_primality #(parameter integer W = 8) (
    input wire clk, rst, start,
    input wire [W-1:0] n,
    output reg busy, valid, is_prime
);
    reg [W-1:0] number, divisor;
    always @(posedge clk) begin
        if (rst) begin
            number <= 0;
            divisor <= 2;
            busy <= 0;
            valid <= 0;
            is_prime <= 0;
        end else begin
            valid <= 0;
            if (!busy) begin
                if (start) begin
                    number <= n;
                    divisor <= 2;
                    busy <= 1;
                end
            end else if (number < 2) begin
                is_prime <= 0;
                valid <= 1;
                busy <= 0;
            end else if (divisor > number / divisor) begin
                is_prime <= 1;
                valid <= 1;
                busy <= 0;
            end else if (number % divisor == 0) begin
                is_prime <= 0;
                valid <= 1;
                busy <= 0;
            end else begin
                divisor <= divisor + 1'b1;
            end
        end
    end
endmodule

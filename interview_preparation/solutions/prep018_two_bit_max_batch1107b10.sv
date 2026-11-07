`timescale 1ns/1ps
module prep018_two_bit_max_batch1107b10(
 input wire [1:0] a,b, output wire [1:0] y);
 wire t=a[0]|b[0];
 wire lo_when_a_high_zero=b[1]?b[0]:t;
 wire lo_when_a_high_one=b[1]?t:a[0];
 assign y[1]=a[1]|b[1];
 assign y[0]=a[1]?lo_when_a_high_one:lo_when_a_high_zero;
endmodule

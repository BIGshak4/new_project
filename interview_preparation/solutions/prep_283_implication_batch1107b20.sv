`timescale 1ns/1ps
module prep283_implication_batch1107b20(
 input wire a,b,output wire by_or,by_mux,by_nand);
 wire not_b;
 assign by_or=(~a)|b;
 assign by_mux=a?b:1'b1;
 nand n0(not_b,b,b);
 nand n1(by_nand,a,not_b);
endmodule

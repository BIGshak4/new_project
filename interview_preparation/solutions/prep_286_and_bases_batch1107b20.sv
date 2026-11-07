`timescale 1ns/1ps
module prep286_and_bases_batch1107b20(
 input wire a,b,output wire nand_only,nor_only,mixed);
 wire neg_product,na,nb,mix_neg_product;
 nand n0(neg_product,a,b);
 nand n1(nand_only,neg_product,neg_product);
 nor r0(na,a,a);
 nor r1(nb,b,b);
 nor r2(nor_only,na,nb);
 nand m0(mix_neg_product,a,b);
 nor m1(mixed,mix_neg_product,mix_neg_product);
endmodule

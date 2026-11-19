// Four full-adder cells. Every cell input is a bit of the same weight.
module prep001_fa(input wire a,b,cin, output wire sum,carry);
  assign sum = a ^ b ^ cin;
  assign carry = (a & b) | (cin & (a ^ b));
endmodule
module prep001_popcount7(input wire [6:0] x, output wire [2:0] count);
  wire sa,sb,ca,cb,cc;
  prep001_fa f0(x[0],x[1],x[2],sa,ca);
  prep001_fa f1(x[3],x[4],x[5],sb,cb);
  prep001_fa f2(sa,sb,x[6],count[0],cc);
  prep001_fa f3(ca,cb,cc,count[1],count[2]);
endmodule

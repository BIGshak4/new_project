// Each instance is counted as a full adder, including pins tied to zero.
module prep001_fa(input wire a,b,c, output wire s,k);
  assign s = a ^ b ^ c;
  assign k = (a&b) | (a&c) | (b&c);
endmodule
module prep001_eight_fa_only(input wire [7:0] x, output wire [3:0] y);
  wire s0,s1,s2,c0,c1,c2,c3,t0,u0,u1;
  prep001_fa f0(x[0],x[1],x[2],s0,c0);
  prep001_fa f1(x[3],x[4],x[5],s1,c1);
  prep001_fa f2(s0,s1,x[6],s2,c2);
  prep001_fa f3(s2,x[7],1'b0,y[0],c3);
  prep001_fa f4(c0,c1,c2,t0,u0);
  prep001_fa f5(t0,c3,1'b0,y[1],u1);
  prep001_fa f6(u0,u1,1'b0,y[2],y[3]);
endmodule

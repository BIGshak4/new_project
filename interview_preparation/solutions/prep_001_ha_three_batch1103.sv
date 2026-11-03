`timescale 1ns/1ps
module prep001_ha(input wire a,b, output wire s,c);
  assign s=a^b;
  assign c=a&b;
endmodule
module prep001_ha3(input wire [2:0] x, output wire [1:0] y,
                   output wire unused_carry);
  wire s,c1,c2;
  prep001_ha first(x[0],x[1],s,c1);
  prep001_ha second(s,x[2],y[0],c2);
  prep001_ha carries(c1,c2,y[1],unused_carry);
endmodule

module prep122_ha(input wire a,b, output wire s,k);
  assign s=a^b;
  assign k=a&b;
endmodule
module prep122_fa(input wire a,b,c, output wire s,k);
  assign s=a^b^c;
  assign k=(a&b)|(a&c)|(b&c);
endmodule
module prep122_mixed(input wire [3:0] a,b, output wire [4:0] s);
  wire [2:0] c;
  prep122_ha h0(a[0],b[0],s[0],c[0]);
  prep122_fa f1(a[1],b[1],c[0],s[1],c[1]);
  prep122_fa f2(a[2],b[2],c[1],s[2],c[2]);
  prep122_fa f3(a[3],b[3],c[2],s[3],s[4]);
endmodule

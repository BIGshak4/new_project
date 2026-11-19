// Combinational, unsigned, highest numbered asserted input wins.
module prep349_pe4(input wire [3:0] x, output wire valid, output wire [1:0] code);
  assign valid = |x;
  assign code[1] = x[3] | x[2];
  assign code[0] = x[3] | (~x[2] & x[1]);
endmodule

module prep349_pe16(input wire [15:0] x, output wire valid, output wire [3:0] code);
  wire [3:0] group_valid;
  wire [1:0] local_code [0:3];
  wire [1:0] group_code;
  genvar g;
  generate for (g=0; g<4; g=g+1) begin: groups
    prep349_pe4 cell4(x[4*g +: 4], group_valid[g], local_code[g]);
  end endgenerate
  prep349_pe4 group_encoder(group_valid, valid, group_code);
  assign code = valid ? {group_code, local_code[group_code]} : 4'b0000;
endmodule

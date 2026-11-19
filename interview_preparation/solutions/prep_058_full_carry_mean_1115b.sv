// b is the FULL W+1-bit sum a+2; carry must be preserved by the caller.
// Only bitwise gates implement the mean datapath.
module prep058_full_mean #(parameter W=4)
  (input wire [W-1:0] a,
   input wire [W:0] b,
   output wire [W:0] mean);
  wire parity = a[0];
  wire [W:0] a_ext = {1'b0,a};
  assign mean[0] = ~parity;
  assign mean[W:1] = ({W{~parity}} & a_ext[W:1])
                    | ({W{parity}} & b[W:1]);
endmodule

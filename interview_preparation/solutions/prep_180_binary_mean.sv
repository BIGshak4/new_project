// Unsigned inputs; result = whole + half*0.5, with no addition overflow.
module binary_mean #(parameter int N = 8) (
  input logic [N-1:0] a, b,
  output logic [N-1:0] whole,
  output logic half
);
  logic [N:0] total;
  always_comb begin
    total = {1'b0, a} + {1'b0, b};
    whole = total[N:1];
    half = total[0];
  end
endmodule

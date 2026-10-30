// Valid BCD input0..9; two BCD output digits encode0..27.
module bcd_times_three (
  input logic [3:0] digit,
  output logic valid,
  output logic [3:0] tens, ones
);
  logic [5:0] product;
  always_comb begin
    valid = digit < 4'd10;
    product = {1'b0, digit, 1'b0} + {2'b0, digit};
    tens = 4'd0;
    ones = 4'd0;
    if (valid) begin
      if (product >= 6'd20) begin
        tens = 4'd2;
        ones = product - 6'd20;
      end else if (product >= 6'd10) begin
        tens = 4'd1;
        ones = product - 6'd10;
      end else ones = product;
    end
  end
endmodule

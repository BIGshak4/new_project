// Emits one MSB-first quotient bit for each accepted input bit.
// No finite-width register stores an infinitely growing quotient.
module serial_divide_five (
  input logic clk, rst, valid, bit_in,
  output logic quotient_bit, quotient_valid,
  output logic [2:0] remainder
);
  logic [3:0] trial;
  always_comb trial = {remainder, bit_in};
  always_ff @(posedge clk) begin
    if (rst) begin
      remainder <= 3'd0;
      quotient_bit <= 1'b0;
      quotient_valid <= 1'b0;
    end else begin
      quotient_valid <= valid;
      if (valid) begin
        quotient_bit <= trial >= 4'd5;
        remainder <= trial >= 4'd5 ? trial - 4'd5 : trial;
      end
    end
  end
endmodule

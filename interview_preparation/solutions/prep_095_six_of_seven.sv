// Sliding full windows, registered alarm including the current error sample.
module six_of_seven (
  input logic clk, rst, error_in,
  output logic alarm
);
  logic [6:0] history;
  logic [3:0] count;
  logic [2:0] filled;
  logic [3:0] next_count;
  always_comb next_count = count + {3'b0,error_in} - {3'b0,history[6]};
  always_ff @(posedge clk) begin
    if (rst) begin
      history <= 7'd0; count <= 4'd0; filled <= 3'd0; alarm <= 1'b0;
    end else begin
      history <= {history[5:0],error_in};
      count <= next_count;
      if (filled < 3'd7) filled <= filled + 3'd1;
      alarm <= filled >= 3'd6 && next_count >= 4'd6;
    end
  end
endmodule

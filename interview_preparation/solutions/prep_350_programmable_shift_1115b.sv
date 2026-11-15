// One logical right-shift per cycle after an accepted start; eight-bit word.
module prep350(input wire clk, rst, start,
               input wire [7:0] data,
               input wire [2:0] amount,
               output reg [7:0] result,
               output reg busy, done);
  reg [2:0] remaining;
  always @(posedge clk) begin
    if (rst) begin
      result <= 8'b0;
      remaining <= 3'b0;
      busy <= 1'b0;
      done <= 1'b0;
    end else begin
      done <= 1'b0;
      if (busy) begin
        result <= {1'b0, result[7:1]};
        remaining <= remaining - 3'd1;
        if (remaining == 3'd1) begin
          busy <= 1'b0;
          done <= 1'b1;
        end
      end else if (start) begin
        result <= data;
        remaining <= amount;
        busy <= (amount != 3'd0);
        done <= (amount == 3'd0);
      end
    end
  end
endmodule

// One full input-clock cycle high after each50th rising edge; not a50% clock.
module fiftieth_clock_pulse (
  input logic clk, rst,
  output logic pulse
);
  logic [5:0] phase;
  always_ff @(posedge clk) begin
    if (rst) begin phase <= 6'd0; pulse <= 1'b0; end
    else begin
      pulse <= phase == 6'd49;
      phase <= phase == 6'd49 ? 6'd0 : phase + 6'd1;
    end
  end
endmodule

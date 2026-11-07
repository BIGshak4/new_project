// Signed symmetric Q15 amplitude: +/-32767, not the asymmetric -32768 endpoint.
// Two nonzero ROM constants; zero is supplied by wiring. Quarter-fold has
// three distinct magnitudes if zero is charged as a stored ROM word.
module prep299_sine_rom(input wire clk,rst,en,
                       output reg [3:0] phase,
                       output reg signed [15:0] sample);
  reg [2:0] q,index;
  reg signed [15:0] magnitude;
  always @(posedge clk) begin
    if (rst) phase <= 0;
    else if (en) phase <= (phase==9) ? 0 : phase+1'b1;
  end
  always @* begin
    q = (phase>=5) ? phase-5 : phase;
    index = (q>2) ? 5-q : q;
    case(index)
      0: magnitude=16'sd0;
      1: magnitude=16'sd19260;
      2: magnitude=16'sd31163;
      default: magnitude=16'sd0;
    endcase
    sample = (phase>=5) ? -magnitude : magnitude;
  end
endmodule

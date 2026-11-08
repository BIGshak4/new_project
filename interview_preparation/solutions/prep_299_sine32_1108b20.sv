// Chosen interpretation sin(2*pi*n/32); the literal source's *32 is zero.
// Symmetric signed Q15; zero is wired, eight nonzero magnitudes are stored.
module prep299_sine32(input wire clk,rst,en,
                     output reg [4:0] phase,
                     output reg signed [15:0] sample);
  reg [4:0] index;
  reg signed [15:0] magnitude;
  always @(posedge clk)begin
    if(rst)phase<=0;
    else if(en)phase<=phase+1'b1;
  end
  always @* begin
    index = phase[3:0]>8 ? 16-{1'b0,phase[3:0]} : {1'b0,phase[3:0]};
    case(index)
      0:magnitude=0;
      1:magnitude=6393;
      2:magnitude=12539;
      3:magnitude=18204;
      4:magnitude=23170;
      5:magnitude=27245;
      6:magnitude=30273;
      7:magnitude=32137;
      8:magnitude=32767;
      default:magnitude=0;
    endcase
    sample=phase[4] ? -magnitude : magnitude;
  end
endmodule

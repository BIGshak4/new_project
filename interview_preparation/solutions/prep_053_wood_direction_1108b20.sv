// A is the left sensor (ab[1]); B is the right sensor (ab[0]).
// Short objects: isolated monotone traversals, pauses allowed. Reversal/abort
// requires an external reset at a known boundary. See observability discussion.
// Long objects: complete traversals and observable partial reversals supported.
module prep053_wood_direction #(parameter SHORT_MODE=0)(
  input wire clk,rst,input wire [1:0] ab,
  output reg right_pulse,left_pulse);
  localparam IDLE=0, WAIT_B=1, EXIT_B=2, WAIT_A=3, EXIT_A=4;
  reg [2:0] state,next_state;
  reg go_right,go_left;
  always @* begin
    next_state=state;go_right=0;go_left=0;
    case(state)
      IDLE: case(ab)
        2'b10:next_state=WAIT_B;
        2'b01:next_state=WAIT_A;
        default:next_state=IDLE;
      endcase
      WAIT_B: case(ab)
        2'b01:next_state=EXIT_B;
        2'b00:if(!SHORT_MODE)next_state=IDLE;
        2'b11:if(SHORT_MODE)next_state=IDLE;
        default:next_state=WAIT_B;
      endcase
      EXIT_B: case(ab)
        2'b00:begin next_state=IDLE;go_right=1;end
        2'b11:next_state=SHORT_MODE ? IDLE : WAIT_B;
        2'b10:next_state=IDLE; // Out-of-contract skipped/invalid observation.
        default:next_state=EXIT_B;
      endcase
      WAIT_A: case(ab)
        2'b10:next_state=EXIT_A;
        2'b00:if(!SHORT_MODE)next_state=IDLE;
        2'b11:if(SHORT_MODE)next_state=IDLE;
        default:next_state=WAIT_A;
      endcase
      EXIT_A: case(ab)
        2'b00:begin next_state=IDLE;go_left=1;end
        2'b11:next_state=SHORT_MODE ? IDLE : WAIT_A;
        2'b01:next_state=IDLE;
        default:next_state=EXIT_A;
      endcase
      default:next_state=IDLE;
    endcase
  end
  always @(posedge clk)begin
    if(rst)begin state<=IDLE;right_pulse<=0;left_pulse<=0;end
    else begin state<=next_state;right_pulse<=go_right;left_pulse<=go_left;end
  end
endmodule

// Register-array implementation. W >= 1. One rising-edge clock domain.
// Reset is synchronous and active high; storage contents are not reset.
module fifo8 #(parameter int W = 8) (
  input logic clk, rst, wr_en, rd_en,
  input logic [W-1:0] din,
  output logic [W-1:0] dout,
  output logic rd_valid, full, empty,
  output logic wr_accepted, rd_accepted
);
  logic [W-1:0] mem [0:7];
  logic [2:0] rp, wp;
  logic [3:0] count;
  logic pop, push;
  assign empty = (count == 0);
  assign full  = (count == 8);
  assign pop  = rd_en && !empty;
  assign push = wr_en && (!full || pop);
  // These combinational handshakes describe acceptance at the next edge.
  assign rd_accepted = !rst && pop;
  assign wr_accepted = !rst && push;
  always_ff @(posedge clk) begin
    if (rst) begin
      rp <= 0; wp <= 0; count <= 0;
      dout <= '0; rd_valid <= 0;
    end else begin
      rd_valid <= pop;
      if (pop) begin
        dout <= mem[rp]; // old value with nonblocking register-array semantics
        rp <= rp + 3'd1;
      end
      if (push) begin
        mem[wp] <= din;
        wp <= wp + 3'd1;
      end
      case ({push,pop})
        2'b10: count <= count + 4'd1;
        2'b01: count <= count - 4'd1;
        default: count <= count;
      endcase
    end
  end
endmodule

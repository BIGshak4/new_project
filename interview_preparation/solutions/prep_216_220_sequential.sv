// Proposed synthesizable RTL. Python model verification is reported separately.
// All resets below are synchronous, active high. Inputs sampled on posedge clk.
module prep216_divide(input logic clk, rst, output logic div2, div4);
  always_ff @(posedge clk) begin
    if (rst) begin div2 <= 0; div4 <= 0; end
    else begin div2 <= ~div2; div4 <= div4 ^ div2; end
  end
endmodule

module prep217_moore(input logic clk, rst, bit_valid, bit_in,
                     output logic detected);
  logic [2:0] state, ns;
  always_comb begin
    case (state)
      0: ns = bit_in ? 1 : 0;
      1: ns = bit_in ? 1 : 2;
      2: ns = bit_in ? 3 : 0;
      3: ns = bit_in ? 4 : 2;
      4: ns = bit_in ? 1 : 5;
      5: ns = bit_in ? 6 : 0;
      6: ns = bit_in ? 4 : 2;
      default: ns = 0;
    endcase
  end
  always_ff @(posedge clk) begin
    if (rst) state <= 0;
    else if (bit_valid) state <= ns;
  end
  assign detected = (state == 6);
  // Pure Moore output holds during invalid cycles. If the interface requires
  // one-cycle event pulses despite idle cycles, add an explicit output flag.
endmodule

module prep217_shift(input logic clk, rst, bit_valid, bit_in,
                     output logic detected);
  logic [5:0] window;
  always_ff @(posedge clk) begin
    if (rst) window <= 0;
    else if (bit_valid) window <= {window[4:0],bit_in};
  end
  assign detected = (window == 6'b101101);
endmodule

module prep218_match #(parameter int W=64)(
  input logic clk, rst, load0, load1, sample_valid, pair_mode,
  input logic [W-1:0] enroll_data, sample,
  output logic matched);
  logic [W-1:0] ref0, ref1;
  logic have0, have1, previous_hit;
  logic hit;
  assign hit = (have0 && sample == ref0) || (have1 && sample == ref1);
  always_ff @(posedge clk) begin
    if (rst) begin
      ref0 <= 0; ref1 <= 0; have0 <= 0; have1 <= 0;
      previous_hit <= 0; matched <= 0;
    end else begin
      matched <= 0;
      if (load0 || load1) begin
        if (load0) begin ref0 <= enroll_data; have0 <= 1; end
        if (load1) begin ref1 <= enroll_data; have1 <= 1; end
        previous_hit <= 0;
      end else if (sample_valid) begin
        matched <= hit && (!pair_mode || previous_hit);
        previous_hit <= hit;
      end
    end
  end
  // Freeze pair_mode during an authentication transaction. Configuration wins
  // over samples; invalid sample cycles skip and do not break the streak.
endmodule

module prep219_infix #(parameter int W=16)(
  input logic clk, rst, token_valid,
  input logic [1:0] token_kind, // 0 NUMBER, 1 PLUS, 2 TIMES, 3 EQUAL
  input logic [W-1:0] number,
  output logic token_ready, result_valid, error,
  output logic [W-1:0] result);
  logic [W-1:0] s, p;
  logic expect_number, pending_mul;
  assign token_ready = 1'b1;
  always_ff @(posedge clk) begin
    if (rst) begin
      s <= 0; p <= 0; result <= 0; result_valid <= 0; error <= 0;
      expect_number <= 1; pending_mul <= 0;
    end else begin
      result_valid <= 0; error <= 0;
      if (token_valid) begin
        if (expect_number && token_kind == 0) begin
          p <= pending_mul ? p * number : number;
          expect_number <= 0;
        end else if (!expect_number && token_kind == 1) begin
          s <= s + p; pending_mul <= 0; expect_number <= 1;
        end else if (!expect_number && token_kind == 2) begin
          pending_mul <= 1; expect_number <= 1;
        end else if (!expect_number && token_kind == 3) begin
          result <= s + p; result_valid <= 1;
          s <= 0; p <= 0; pending_mul <= 0; expect_number <= 1;
        end else begin
          error <= 1; s <= 0; p <= 0;
          pending_mul <= 0; expect_number <= 1;
        end
      end
    end
  end
endmodule

module prep220_memory #(parameter int W=8)(
  input logic clk, rst, wr_en, re_en,
  input logic [1:0] wr_addr, re_addr,
  input logic [W-1:0] wr_data,
  output logic [W-1:0] read_data,
  output logic Valid);
  logic [W-1:0] words [0:3];
  integer i;
  always_ff @(posedge clk) begin
    if (rst) begin
      for (i=0; i<4; i=i+1) words[i] <= '0;
      read_data <= '0; Valid <= 0;
    end else begin
      Valid <= re_en;
      if (re_en) read_data <= words[re_addr]; // old word on collision
      if (wr_en) words[wr_addr] <= wr_data;
    end
  end
endmodule

module prep036_left_mod3(input logic clk, rst, bit_valid, bit_in,
                         output logic divisible, output logic [1:0] state);
  logic seen;
  always_ff @(posedge clk) begin
    if (rst) begin state <= 0; seen <= 0; end
    else if (bit_valid) begin
      seen <= 1;
      case (state)
        0: state <= bit_in ? 2 : 0;
        1: state <= bit_in ? 1 : 2;
        2: state <= bit_in ? 0 : 1;
        default: state <= 0;
      endcase
    end
  end
  assign divisible = seen && (state == 0);
endmodule

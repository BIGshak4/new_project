module digital1118b_tb;
  reg a, b, c;
  reg [3:0] d;
  reg [1:0] s;
  wire logic_result, difference, selected;
  integer i;
  complementary_aoi21 device(a, b, c, logic_result);
  selector_xor xor_cell(a, b, difference);
  selector_tree tree(d, s, selected);
  initial begin
    for (i=0; i<8; i=i+1) begin
      {a,b,c}=i;
      #1;
      if (logic_result !== ~((a & b) | c) || difference !== (a ^ b))
        $fatal(1, "unexpected gate result at %d", i);
    end
    for (i=0; i<64; i=i+1) begin
      {d,s}=i;
      #1;
      if (selected !== d[s])
        $fatal(1, "mismatched select at %d", i);
    end
    $display("PASS: AOI21, XOR, four-channel selector");
    $finish;
  end
endmodule

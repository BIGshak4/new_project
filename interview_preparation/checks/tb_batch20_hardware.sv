module tb;
  reg [3:0] x; reg [1:0] mode; wire predicate;
  controlled_predicates cp(x,mode,predicate);
  reg [7:0] d8; reg [2:0] s8; wire balanced,optimized;
  mux8_late mx(d8,s8,balanced,optimized);
  wire decode_y; wire [7:0] decoded;
  decoder_mux #(3) dm(d8,s8,decode_y,decoded);
  reg [1:0] d2; reg s2; wire y2; wire [1:0] dec2;
  decoder_mux #(1) dm1(d2,s2,y2,dec2);
  reg [3:0] d4; reg [1:0] s4; wire y4; wire [3:0] dec4;
  decoder_mux #(2) dm2(d4,s4,y4,dec4);
  reg [15:0] d16; reg [3:0] s16; wire y16; wire [15:0] dec16;
  decoder_mux #(4) dm4(d16,s16,y16,dec16);
  reg clk,live_d; wire rise_only,fall_only,both_edges;
  live_edge_polarities edge_dut(clk,live_d,rise_only,fall_only,both_edges);
  integer i,j,k,count,expected,checks;
  reg saved;
  reg [31:0] random_word;
  task verify_edges;
    begin
      #1;
      if(rise_only !== (live_d && !saved) || fall_only !== (!live_d && saved) ||
         both_edges !== (live_d != saved)) $fatal(1,"edge mismatch");
      checks=checks+1;
    end
  endtask
  initial begin
    checks=0; x=0;mode=0;d8=0;s8=0;d2=0;s2=0;d4=0;s4=0;d16=0;s16=0;
    clk=0;live_d=0;saved=0;
    #1;clk=1;verify_edges;clk=0;
    for(i=0;i<16;i=i+1) begin
      count=0;for(k=0;k<4;k=k+1) count=count+((i>>k)&1);
      for(j=0;j<4;j=j+1) begin
        x=i;mode=j;#1;
        case(j) 0:expected=(count<4);1:expected=(count>2);2:expected=count%2;3:expected=1-count%2;endcase
        if(predicate !== expected[0]) $fatal(1,"predicate %d/%d",i,j);
        checks=checks+1;
      end
    end
    for(i=0;i<256;i=i+1) for(j=0;j<8;j=j+1) begin
      d8=i;s8=j;#1;
      if(balanced !== d8[j] || optimized !== d8[j] || decode_y !== d8[j] ||
         decoded !== (8'b1 << j)) $fatal(1,"mux8 %d/%d",i,j);
      checks=checks+1;
    end
    for(i=0;i<4;i=i+1) for(j=0;j<2;j=j+1) begin
      d2=i;s2=j;#1;if(y2 !== d2[j] || dec2 !== (2'b1<<j)) $fatal(1,"decoder1");checks=checks+1;
    end
    for(i=0;i<16;i=i+1) for(j=0;j<4;j=j+1) begin
      d4=i;s4=j;#1;if(y4 !== d4[j] || dec4 !== (4'b1<<j)) $fatal(1,"decoder2");checks=checks+1;
    end
    // Every sixteen-bit vector and every select at N=4.
    for(i=0;i<65536;i=i+1) for(j=0;j<16;j=j+1) begin
      d16=i;s16=j;#1;if(y16 !== d16[j] || dec16 !== (16'b1<<j)) $fatal(1,"decoder4");checks=checks+1;
    end
    // Independent last-sample oracle, including repeated changes before edges.
    random_word=32'h4c09b137;
    for(i=0;i<4096;i=i+1) begin
      random_word=random_word*32'd1664525+32'd1013904223;
      if(random_word[4:3]==0) begin clk=1;saved=live_d;verify_edges;clk=0;end
      else begin live_d=random_word[8];verify_edges;end
    end
    $display("PASS batch20 hardware checks=%0d",checks);
    $finish;
  end
endmodule

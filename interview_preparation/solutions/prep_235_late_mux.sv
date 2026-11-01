module late_mux2(input wire low,high,select, output wire y);
  assign y = select ? high : low;
endmodule

module mux8_late(input wire [7:0] d, input wire [2:0] s,
                 output wire balanced, optimized);
  wire p01,p23,p45,p67,lo,hi;
  late_mux2 b0(d[0],d[1],s[0],p01);
  late_mux2 b1(d[2],d[3],s[0],p23);
  late_mux2 b2(d[4],d[5],s[0],p45);
  late_mux2 b3(d[6],d[7],s[0],p67);
  late_mux2 b4(p01,p23,s[1],lo);
  late_mux2 b5(p45,p67,s[1],hi);
  late_mux2 b6(lo,hi,s[2],balanced);

  // Shared p23,p45,p67,hi are four cells also used by the separate optimized
  // topology. Counting each design in isolation gives seven MUX cells each.
  wire lo_without_d0, rest;
  wire choose_d0 = ~|s;
  late_mux2 o0(d[1],p23,s[1],lo_without_d0);
  late_mux2 o1(lo_without_d0,hi,s[2],rest);
  late_mux2 o2(rest,d[0],choose_d0,optimized);
endmodule

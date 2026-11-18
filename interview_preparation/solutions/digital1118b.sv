// Educational settled-state switch and Boolean models.
module complementary_aoi21(input wire a, b, c, output wire f);
  supply1 vdd;
  supply0 gnd;
  wire upper, lower;
  pmos (upper, vdd, a);
  pmos (upper, vdd, b);
  pmos (f, upper, c);
  nmos (lower, gnd, b);
  nmos (f, lower, a);
  nmos (f, gnd, c);
endmodule

module selector_cell(input wire s, d0, d1, output wire y);
  wire ns, low_term, high_term;
  not (ns, s);
  and (low_term, ns, d0);
  and (high_term, s, d1);
  or (y, low_term, high_term);
endmodule

module selector_xor(input wire a, b, output wire y);
  wire nb;
  not (nb, b);
  selector_cell mux(a, b, nb, y);
endmodule

module selector_tree(input wire [3:0] d, input wire [1:0] s, output wire y);
  wire low_pair, high_pair;
  selector_cell low(s[0], d[0], d[1], low_pair);
  selector_cell high(s[0], d[2], d[3], high_pair);
  selector_cell last(s[1], low_pair, high_pair, y);
endmodule

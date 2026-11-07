// Ideal connectivity abstraction only; no threshold, delay, body diode or SPICE.
module prep302_cmos_nand(input wire a,b, output wire y);
  supply1 vdd;
  supply0 gnd;
  wire middle;
  pmos pa(y,vdd,a);
  pmos pb(y,vdd,b);
  nmos na(y,middle,a);
  nmos nb(middle,gnd,b);
endmodule

`timescale 1ns/1ps
// IDEAL digital switch abstraction only: no threshold loss or analog signoff.
module prep282_ideal_switch_xor_batch1107b20(
 input wire a,b,output wire y,output wire x);
 pmos first_p(x,1'b1,a);
 nmos first_n(x,1'b0,a);
 // These are signal-connected diffusion terminals, not fixed VDD/GND rails.
 pmos second_p(y,a,b);
 nmos second_n(y,x,b);
endmodule

`timescale 1ns/1ps
// Supplied box model shown only to reproduce its specified interface.
module prep152_box(input wire clk,load, input wire [3:0] a,
                   output reg [3:0] q);
  always @(posedge clk) begin
    if(load) q<=a;
    else q<=q+4'd1;
  end
endmodule
module prep152_loaded(input wire clk,load, input wire [4:0] a,
                      output wire [4:0] q);
  wire [3:0] low;
  reg high;
  prep152_box supplied(clk,load,a[3:0],low);
  always @(posedge clk) begin
    if(load) high<=a[4];
    else high<=high ^ (&low);
  end
  assign q={high,low};
endmodule

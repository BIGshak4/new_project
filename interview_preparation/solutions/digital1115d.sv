// Educational synchronous RTL. All controls meet setup/hold; no CDC is inferred.
module prep207_detect1010(input wire clk,rst,x,output reg hit);
  reg [1:0] prefix;
  // prefix is the longest proper prefix of 1010 that is a suffix of history.
  always @(posedge clk) begin
    if (rst) begin prefix<=0; hit<=0; end
    else begin
      hit<=0;
      case (prefix)
        0: prefix <= x ? 1 : 0;
        1: prefix <= x ? 1 : 2;
        2: prefix <= x ? 3 : 0;
        3: if(x) prefix<=1; else begin prefix<=2;hit<=1;end
      endcase
    end
  end
endmodule

// Zero-delay OR/NOT in the specified weighted-delay thought experiment.
// Two-input gate fan-in; the loop creates an acyclic higher-bit OR chain.
module prep014_weighted_msb(input wire [7:0] x,output wire [7:0] y);
  wire [6:0] higher;
  assign higher[6]=x[7];
  genvar i;
  generate for(i=0;i<6;i=i+1) begin: prefix_or
    assign higher[i]=higher[i+1] | x[i+1];
  end endgenerate
  assign y[7]=x[7];
  assign y[6:0]=x[6:0] & ~higher;
endmodule

module prep042_stretch #(parameter integer N=3,
                         parameter integer CW=(N<2 ? 1 : $clog2(N+1)))
 (input wire clk,rst,x,output wire y);
  reg previous;
  reg [CW-1:0] remaining;
  initial if(N<1) $fatal(1,"N must be positive");
  always @(posedge clk) begin
    if(rst) begin previous<=0;remaining<=0;end
    else begin
      previous<=x;
      if(x && !previous) remaining<=N;
      else if(remaining!=0) remaining<=remaining-1'b1;
    end
  end
  assign y=(remaining!=0);
endmodule

// A cooling fan: hot alone starts it, cold alone stops it; deadband retains.
// Contradictory sensors force OFF for the fault interval; reset also forces OFF.
module prep_thermal1115d(input wire clk,rst,hot,cold,
                        output reg fan_on,output wire sensor_fault);
  assign sensor_fault=hot & cold;
  always @(posedge clk) begin
    if(rst || sensor_fault) fan_on<=0;
    else if(hot) fan_on<=1;
    else if(cold) fan_on<=0;
  end
endmodule

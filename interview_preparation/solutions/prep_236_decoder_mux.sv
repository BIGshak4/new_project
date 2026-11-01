module decoder_mux #(parameter integer N=3)(
  input wire [(1<<N)-1:0] d, input wire [N-1:0] s,
  output wire y, output wire [(1<<N)-1:0] decoded);
  wire [(1<<N)-1:0] terms;
  genvar k;
  generate for(k=0;k<(1<<N);k=k+1) begin: lane
    assign decoded[k] = (s == k);
    assign terms[k] = d[k] & decoded[k];
  end endgenerate
  assign y = |terms;
endmodule

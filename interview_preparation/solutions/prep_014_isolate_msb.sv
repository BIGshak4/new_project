// Fixed right shifts are zero-filled wiring, not variable barrel shifters.
// Pure combinational logic; vector outputs remain eight bits wide.
module isolate_msb8 (
    input  wire [7:0] x,
    output wire [7:0] y
);
    wire [7:0] s1, s2, s3;
    assign s1 = x  | (x  >> 1);
    assign s2 = s1 | (s1 >> 2);
    assign s3 = s2 | (s2 >> 4);
    assign y  = s3 ^ (s3 >> 1);
endmodule

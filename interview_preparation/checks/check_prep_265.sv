`timescale 1ns/1ps
module check_prep_265;
    reg clk=0, rst=1, start=0;
    reg [11:0] n=0;
    wire busy,valid,is_prime;
    integer value,cycles,checks=0;
    prep_265_primality #(.W(12)) dut(clk,rst,start,n,busy,valid,is_prime);
    always #5 clk=~clk;
    function integer oracle(input integer x);
        integer d;
        begin
            oracle=(x>=2);
            for(d=2;d*d<=x;d=d+1)
                if(x%d==0) oracle=0;
        end
    endfunction
    initial begin
        @(posedge clk); #1;
        if(busy || valid || is_prime) $fatal(1,"reset");
        @(negedge clk); rst=0;
        for(value=0;value<4096;value=value+1) begin
            @(negedge clk); n=value; start=1;
            @(posedge clk); #1;
            if(!busy || valid) $fatal(1,"accept");
            @(negedge clk); start=0; n=4095-value;
            cycles=0;
            while(!valid) begin
                @(posedge clk); #1; cycles=cycles+1;
                if(cycles>66) $fatal(1,"termination");
            end
            if(busy || is_prime!==oracle(value)) $fatal(1,"result %0d",value);
            checks=checks+1;
            @(posedge clk); #1;
            if(valid) $fatal(1,"valid must be a pulse");
        end
        @(negedge clk); n=4093; start=1;
        @(posedge clk); #1;
        @(negedge clk); rst=1; start=1;
        @(posedge clk); #1;
        if(busy || valid || is_prime) $fatal(1,"reset overrides request");
        $display("PREP-265: %0d exhaustive 12-bit results; reset, capture and valid passed",checks);
        $finish;
    end
endmodule

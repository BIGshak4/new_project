module prep_reasoning_batch1107n30_tb;
    reg clk=0, rst=1, bit_in=0;
    reg [1:0] event_code=0;
    wire [1:0] value, occupancy;
    wire lamp, rejected, divisible;
    integer cases=0, n, code, k, old_count, expected, word, prefix, power;
    reg expected_flag;
    prep292_counter0121 count_dut(clk,rst,value);
    prep301_room room_dut(clk,rst,event_code,lamp,rejected,occupancy);
    prep036_left_div3_lag div_dut(clk,rst,bit_in,divisible);
    prep291_router_driver router();
    task tick; begin #1;clk=1;#1;clk=0;#1;end endtask
    task reset_all; begin rst=1;event_code=0;tick();rst=0;end endtask
    initial begin
        reset_all();
        for(k=0;k<1024;k=k+1)begin
            expected=(k%4==0)?0:((k%4==2)?2:1);
            if(value!==expected[1:0])$fatal(1,"counter mismatch");
            cases=cases+1;tick();
        end
        for(n=0;n<4;n=n+1)for(code=0;code<4;code=code+1)begin
            reset_all();event_code=1;
            for(k=0;k<n;k=k+1)tick();
            event_code=code;#1;
            expected=(code==3)||(code==1&&n==3)||(code==2&&n==0);
            if(rejected!==expected[0])$fatal(1,"pre-edge rejection mismatch");
            old_count=n;
            if(!expected)begin if(code==1)old_count=n+1;if(code==2)old_count=n-1;end
            tick();
            if(occupancy!==old_count[1:0]||lamp!==(old_count!=0))$fatal(1,"room mismatch");
            cases=cases+1;
        end
        for(n=1;n<=10;n=n+1)for(word=0;word<(1<<n);word=word+1)begin
            reset_all();prefix=0;power=1;
            for(k=0;k<n;k=k+1)begin
                expected_flag=(k!=0)&&(prefix%3==0);
                bit_in=(word>>k)&1;tick();
                if(divisible!==expected_flag)$fatal(1,"lagged divisibility mismatch");
                prefix=prefix+bit_in*power;power=power*2;cases=cases+1;
            end
        end
        for(n=1;n<=16;n=n+1)begin
            for(k=0;k<32;k=k+1)begin
                router.run_test(2*n+k,n,32'h12345678+k+n);cases=cases+1;
            end
            router.run_test(65537+2*n,n,32'h87654321+n);cases=cases+1;
            router.run_test(1000000,n,32'h13579bdf+n);cases=cases+1;
        end
        for(k=1;k<=128;k=k+1)begin router.random_test(1000000,k);cases=cases+1;end
        $display("PASS reasoning batch1107n30 %0d cases",cases);$finish;
    end
endmodule

// Testbench body. build_batch20_sequential_tb.py prepends the exact RTL source
// to produce a self-contained compilation unit for a remote HDL runner.
`timescale 1ns/1ps
module tb;
  logic clk=0;
  logic r16=1, d2,d4;
  prep216_divide divdut(clk,r16,d2,d4);
  logic r17=1, bv=0, bi=0, moore_detect, shift_detect;
  prep217_moore fsm(clk,r17,bv,bi,moore_detect);
  prep217_shift shiftreg(clk,r17,bv,bi,shift_detect);
  logic r18=1, load0=0, load1=0, sample_valid=0, pair_mode=0, matched;
  logic [63:0] enroll_data=0, sample=0;
  prep218_match matcher(clk,r18,load0,load1,sample_valid,pair_mode,enroll_data,sample,matched);
  logic r19=1, tv=0, tr, rv, er;
  logic [1:0] kind=0;
  logic [7:0] num=0, result;
  prep219_infix #(.W(8)) expr(clk,r19,tv,kind,num,tr,rv,er,result);
  logic r20=1, we=0, re=0, wd=0, rd, valid_mem;
  logic [1:0] wa=0, ra=0;
  prep220_memory #(.W(1)) memorydut(clk,r20,we,re,wa,ra,wd,rd,valid_mem);
  logic r36=1, v36=0, b36=0, divisible;
  logic [1:0] state36;
  prep036_left_mod3 leftdut(clk,r36,v36,b36,divisible,state36);

  integer i,j,k,n,v,hist,expected,case_count,stream_count,prefix_count;
  integer c, waddr,wdata,wen,raddr,ren,prev_data,prev_valid,res;
  integer old_word,expected_data,expected_word;
  integer left_value, exponent, expected_s;
  integer expr_case, terms, product, value, op, term_count;
  integer hit_now, previous_hit, expect_match, mode;
  logic [63:0] enrolled0, enrolled1;
  logic [63:0] mix_value;

  task automatic tick;
    begin #5; clk=1; #1; clk=0; #4; end
  endtask
  task automatic number_token(input integer value_in);
    begin
      tv=1; kind=0; num=value_in; tick();
      if (er || rv || !tr) $fatal(1,"number handshake/error");
      tv=0; tick();
      if (er || rv) $fatal(1,"idle after number");
    end
  endtask
  task automatic operator_token(input integer op_in);
    begin
      tv=1; kind=op_in; tick();
      if (er || rv || !tr) $fatal(1,"operator handshake/error");
      tv=0; tick();
    end
  endtask

  initial begin
    $display("BEGIN PREP-216");
    tick();
    r16=0;
    for(i=1;i<=128;i=i+1) begin
      tick();
      if (d2 !== (i%2) || d4 !== ((i/2)%2)) $fatal(1,"divider edge %0d",i);
    end
    for(j=0;j<4;j=j+1) begin
      r16=1; tick(); r16=0;
      for(k=0;k<j;k=k+1) tick();
      r16=1;tick();
      if(d2 !== 0 || d4 !== 0) $fatal(1,"divider reset");
    end
    $display("PREP-216 PASS 128 edges + 4 phase resets");

    $display("BEGIN PREP-217");
    prefix_count=0;stream_count=0;
    for(n=0;n<=8;n=n+1) begin
      for(v=0;v<(1<<n);v=v+1) begin
        r17=1; bv=0; tick(); r17=0; hist=0;
        if(moore_detect !== 0 || shift_detect !== 0) $fatal(1,"detector reset");
        for(i=0;i<n;i=i+1) begin
          bv=1; bi=(v>>(n-1-i))&1;
          hist=((hist<<1)|bi)&63;
          tick(); expected=(i>=5 && hist==45);
          if(moore_detect !== expected || shift_detect !== expected)
            $fatal(1,"detector n%0d v%0d i%0d",n,v,i);
          prefix_count=prefix_count+1;
        end
        // Pure Moore/window outputs hold their last level on invalid cycles.
        bv=0; expected=moore_detect; tick();
        if(moore_detect !== expected || shift_detect !== expected) $fatal(1,"detector hold");
        stream_count=stream_count+1;
      end
    end
    r17=1; bv=0; tick(); r17=0; hist=0; v=9'b101101101;
    for(i=0;i<9;i=i+1) begin
      bv=1;bi=(v>>(8-i))&1;tick();expected=(i==5 || i==8);
      if(moore_detect !== expected || shift_detect !== expected) $fatal(1,"detector overlap at%0d",i+1);
    end
    r17=1; bv=0;
    $display("PREP-217 PASS %0d streams %0d prefixes + overlap positions6,9",stream_count,prefix_count);

    $display("BEGIN PREP-218");
    // Full 64-bit datapath, including enrolled zero and the top bit.
    enrolled0=64'h0; enrolled1=64'h8000000000000001;
    case_count=0;
    for(mode=0;mode<2;mode=mode+1) begin
      r18=1; sample_valid=0; tick(); r18=0; pair_mode=mode;
      sample=0; sample_valid=1; tick();
      if(matched !== 0) $fatal(1,"empty slot matched zero");
      sample_valid=0; load0=1; enroll_data=enrolled0; tick(); load0=0;
      load1=1; enroll_data=enrolled1; tick(); load1=0;
      previous_hit=0;
      for(i=0;i<256;i=i+1) begin
        case(i%5)
          0,1: mix_value=enrolled0;
          2: mix_value=enrolled1;
          3: mix_value=64'hffffffffffffffff;
          default: mix_value=(64'h9e3779b97f4a7c15*i)^64'h12345678abcdef00;
        endcase
        sample=mix_value; sample_valid=1;
        hit_now=(mix_value==enrolled0 || mix_value==enrolled1);
        expect_match=hit_now && (!mode || previous_hit);
        tick();
        if(matched !== expect_match) $fatal(1,"matcher mode%0d index%0d",mode,i);
        previous_hit=hit_now;
        sample_valid=0; sample=~mix_value; tick();
        if(matched !== 0) $fatal(1,"matcher invalid emitted event");
        case_count=case_count+1;
      end
    end
    r18=1;sample_valid=0;tick();
    if(matched !== 0) $fatal(1,"matcher reset");
    $display("PREP-218 PASS %0d accepted 64-bit samples + idle/reset/enrollment",case_count);

    $display("BEGIN PREP-219");
    // Independent oracle explicitly finishes multiplication runs.
    r19=0;case_count=0;
    for(expr_case=0;expr_case<256;expr_case=expr_case+1) begin
      terms=0; product=(expr_case*29+7)&255;
      number_token(product);
      for(j=0;j<5;j=j+1) begin
        op=(expr_case>>j)&1;
        value=(expr_case*(j+3)+j*17)&255;
        if(op) begin
          operator_token(2); product=product*value;
        end else begin
          operator_token(1); terms=terms+product; product=value;
        end
        // Oracle may reduce freely modulo256; preserve exact bounded ints.
        product=product&255;terms=terms&255;
        number_token(value);
      end
      tv=1;kind=3;tick();
      if(!rv || er || result !== ((terms+product)&255)) $fatal(1,"infix oracle %0d",expr_case);
      tv=0;tick();if(rv || er) $fatal(1,"result not a pulse");
      case_count=case_count+1;
    end
    tv=1;kind=3;tick(); if(!er || rv) $fatal(1,"empty expression accepted");
    tv=0;tick();
    number_token(2);operator_token(1);number_token(3);operator_token(2);number_token(4);
    tv=1;kind=3;tick();if(!rv || result !== 14) $fatal(1,"precedence counterexample");
    tv=0;r19=1;tick();
    if(rv || er || result !== 0) $fatal(1,"infix reset");
    $display("PREP-219 PASS %0d six-operand expressions + grammar/reset/precedence",case_count);

    $display("BEGIN PREP-220");
    // Inject every pre-edge memory and output state; all pin combinations.
    case_count=0;
    for(c=0;c<16;c=c+1)
    for(waddr=0;waddr<4;waddr=waddr+1)
    for(wdata=0;wdata<2;wdata=wdata+1)
    for(wen=0;wen<2;wen=wen+1)
    for(raddr=0;raddr<4;raddr=raddr+1)
    for(ren=0;ren<2;ren=ren+1)
    for(prev_data=0;prev_data<2;prev_data=prev_data+1)
    for(prev_valid=0;prev_valid<2;prev_valid=prev_valid+1)
    for(res=0;res<2;res=res+1) begin
      memorydut.words[0]=(c>>0)&1;memorydut.words[1]=(c>>1)&1;
      memorydut.words[2]=(c>>2)&1;memorydut.words[3]=(c>>3)&1;
      memorydut.read_data=prev_data;memorydut.Valid=prev_valid;
      wa=waddr;wd=wdata;we=wen;ra=raddr;re=ren;r20=res;
      expected_data=res ? 0 : ren ? ((c>>raddr)&1) : prev_data;
      expected=res ? 0 : ren;
      tick();
      if(rd !== expected_data || valid_mem !== expected) $fatal(1,"memory output case%0d",case_count);
      for(k=0;k<4;k=k+1) begin
        expected_word=res ? 0 : (wen && waddr==k) ? wdata : ((c>>k)&1);
        if(memorydut.words[k] !== expected_word) $fatal(1,"memory word case%0d word%0d",case_count,k);
      end
      case_count=case_count+1;
    end
    r20=1;we=0;re=0;
    $display("PREP-220 PASS %0d exhaustive W=1 pre-edge transitions",case_count);

    $display("BEGIN PREP-036");
    prefix_count=0;stream_count=0;
    for(n=0;n<=8;n=n+1) begin
      for(v=0;v<(1<<n);v=v+1) begin
        r36=1;v36=0;tick();r36=0;left_value=0;
        if(divisible !== 0 || state36 !== 0) $fatal(1,"left reset/seen");
        for(i=0;i<n;i=i+1) begin
          v36=1;b36=(v>>(n-1-i))&1;
          left_value=left_value+(b36<<i);
          expected_s=(left_value * (((i+1)%2) ? 2 : 1))%3;
          tick();
          if(state36 !== expected_s || divisible !== (left_value%3==0))
            $fatal(1,"left numeric invariant n%0d v%0d i%0d",n,v,i);
          prefix_count=prefix_count+1;
        end
        v36=0;expected_s=state36;expected=divisible;tick();
        if(state36 !== expected_s || divisible !== expected) $fatal(1,"left hold");
        stream_count=stream_count+1;
      end
    end
    r36=1;v36=0;
    $display("PREP-036 PASS %0d streams %0d numeric-invariant prefixes",stream_count,prefix_count);
    $display("ALL BATCH20 SEQUENTIAL RTL CHECKS PASSED");
    $finish;
  end
endmodule

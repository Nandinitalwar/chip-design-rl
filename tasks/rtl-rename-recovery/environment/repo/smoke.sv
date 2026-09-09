module smoke;
    localparam PW=5;
    reg clk=0,rst=0,downstream_ready=1;
    reg [1:0] dispatch_valid=0,dispatch_dst_we=0,dispatch_branch=0;
    reg [15:0] dispatch_id=0;
    reg [5:0] dispatch_src_a=0,dispatch_src_b=0,dispatch_dst=0;
    wire [1:0] dispatch_accept,renamed_src_a_ready,renamed_src_b_ready;
    wire [9:0] renamed_src_a,renamed_src_b,renamed_dst,renamed_stale;
    reg [1:0] complete_valid=0,retire_ready=0;
    reg [15:0] complete_id=0;
    reg [9:0] complete_dst=0;
    reg resolve_valid=0,resolve_recover=0;
    reg [7:0] resolve_id=0;
    wire [1:0] retire_valid,retire_dst_we,retire_branch;
    wire [15:0] retire_id;
    wire [5:0] retire_arch_dst;
    wire [9:0] retire_dst,retire_stale;
    reg [4:0] allocated;
    rename_recovery dut(.*);
    initial begin
        #1; rst=1;
        #2;if(dispatch_accept!==0 || retire_valid!==0) $fatal(1,"reset gating");
        clk=1;#2;clk=0;rst=0;
        dispatch_valid=1;dispatch_dst_we=1;dispatch_dst=1;dispatch_id=1;
        #2;if(dispatch_accept!==1 || renamed_src_a[4:0]!==0 || !renamed_src_a_ready[0]) $fatal(1,"single rename");
        allocated=renamed_dst[4:0];
        if(allocated<8 || allocated>=24) $fatal(1,"illegal allocation");
        clk=1;#2;clk=0;
        dispatch_dst_we=0;dispatch_src_a=1;dispatch_id=2;
        #2;if(renamed_src_a[4:0]!==allocated || renamed_src_a_ready[0]!==0) $fatal(1,"dependent consumer");
        $display("PUBLIC_SMOKE_PASSED");$finish;
    end
endmodule

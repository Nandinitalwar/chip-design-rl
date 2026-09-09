module smoke;
    reg clk=0,rst=0,downstream_ready=1;
    reg [1:0] dispatch_valid=0,dispatch_dst_we=0,dispatch_branch=0,dispatch_move=0;
    reg [15:0] dispatch_id=0;
    reg [5:0] dispatch_src_a=0,dispatch_src_b=0,dispatch_dst=0;
    wire [1:0] dispatch_accept,renamed_src_a_ready,renamed_src_b_ready;
    wire [9:0] renamed_src_a,renamed_src_b,renamed_dst,renamed_stale;
    reg [1:0] complete_valid=0,retire_ready=0;
    reg [15:0] complete_id=0;
    reg [9:0] complete_dst=0;
    reg resolve_valid=0,resolve_recover=0;
    reg [7:0] resolve_id=0;
    wire [1:0] retire_valid,retire_dst_we,retire_branch,retire_move;
    wire [15:0] retire_id;
    wire [5:0] retire_arch_dst;
    wire [9:0] retire_dst,retire_stale;
    reg [4:0] tag;
    rename_recovery dut(.*);
    task edge_cycle; begin #1;clk=1;#1;clk=0;#1;end endtask
    initial begin
        #1;rst=1;#1;if(dispatch_accept!==0 || retire_valid!==0) $fatal(1,"reset");
        edge_cycle();rst=0;dispatch_valid=1;dispatch_dst_we=1;dispatch_dst=1;dispatch_id=7;
        #1;if(dispatch_accept!==1) $fatal(1,"single ordinary admission");
        tag=renamed_dst[4:0];if(tag<8 || tag>=24) $fatal(1,"allocation");
        edge_cycle();dispatch_valid=0;complete_valid=2;complete_id={8'd7,8'd0};complete_dst={tag,5'b0};
        #1;if(retire_valid!==0) $fatal(1,"no completion bypass");
        edge_cycle();complete_valid=0;
        #1;if(retire_valid!==1 || retire_id[7:0]!==7 || retire_move!==0) $fatal(1,"port1 completion");
        edge_cycle();#1;if(retire_id[7:0]!==7 || retire_dst[4:0]!==tag) $fatal(1,"held record");
        retire_ready=1;edge_cycle();retire_ready=0;
        dispatch_valid=1;dispatch_dst_we=0;dispatch_id=8;dispatch_src_a=1;
        #1;if(dispatch_accept!==1 || renamed_src_a[4:0]!==tag || renamed_src_a_ready[0]!==1) $fatal(1,"committed source");
        $display("PUBLIC_LEGACY_SMOKE_PASSED");$finish;
    end
endmodule

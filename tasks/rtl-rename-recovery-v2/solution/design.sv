module rename_recovery #(parameter integer PHYS=24, ROB=16, PW=$clog2(PHYS)) (
    input wire clk, rst, downstream_ready,
    input wire [1:0] dispatch_valid,
    input wire [15:0] dispatch_id,
    input wire [5:0] dispatch_src_a, dispatch_src_b, dispatch_dst,
    input wire [1:0] dispatch_dst_we, dispatch_branch, dispatch_move,
    output reg [1:0] dispatch_accept,
    output wire [2*PW-1:0] renamed_src_a, renamed_src_b,
    output wire [1:0] renamed_src_a_ready, renamed_src_b_ready,
    output wire [2*PW-1:0] renamed_dst,
    output wire [2*PW-1:0] renamed_stale,
    input wire [1:0] complete_valid,
    input wire [15:0] complete_id,
    input wire [2*PW-1:0] complete_dst,
    input wire resolve_valid,
    input wire [7:0] resolve_id,
    input wire resolve_recover,
    input wire [1:0] retire_ready,
    output reg [1:0] retire_valid,
    output reg [15:0] retire_id,
    output reg [1:0] retire_dst_we, retire_branch, retire_move,
    output reg [5:0] retire_arch_dst,
    output reg [2*PW-1:0] retire_dst, retire_stale
);
    localparam RW=16+2*PW;
    // Record packed as {move,resolved,done,stale,new,branch,we,arch,id}.
    localparam AR=8, WE=11, BR=12, NEW=13, OLD=13+PW, DN=13+2*PW, RS=14+2*PW, MV=15+2*PW;
    reg [RW-1:0] q [0:ROB-1], nq [0:ROB-1];
    reg [31:0] count, next_count;
    reg [8*PW-1:0] committed, next_committed;
    wire [ROB-1:0] qwe, qdone, qmove;
    wire [ROB*3-1:0] qarch;
    wire [ROB*PW-1:0] qdst;
    genvar g;
    generate for(g=0;g<ROB;g=g+1) begin: unpack_record
        assign qwe[g]=q[g][WE];
        assign qdone[g]=q[g][DN];
        assign qmove[g]=q[g][MV];
        assign qarch[g*3 +: 3]=q[g][AR +: 3];
        assign qdst[g*PW +: PW]=q[g][NEW +: PW];
    end endgenerate
    wire [PHYS-1:0] owned, ready;
    wire [31:0] free_count;
    wire [PW-1:0] choice0, choice1;
    wire [1:0] effective;
    assign effective[0]=dispatch_dst_we[0] && dispatch_dst[2:0]!=0;
    assign effective[1]=dispatch_dst_we[1] && dispatch_dst[5:3]!=0;
    rename_ownership #(.PHYS(PHYS),.ROB(ROB)) ownership (
        .committed(committed),.count(count),.has_dst(qwe),.done(qdone),.is_move(qmove),.dst(qdst),
        .owned(owned),.ready(ready),.free_count(free_count),.choice0(choice0),.choice1(choice1));
    rename_map #(.PHYS(PHYS),.ROB(ROB)) mapping (
        .committed(committed),.count(count),.has_dst(qwe),.arch(qarch),.dst(qdst),.ready(ready),
        .accept(dispatch_accept),.effective(effective),.move(dispatch_move),.src_a(dispatch_src_a),.src_b(dispatch_src_b),
        .new_arch(dispatch_dst),.choice0(choice0),.choice1(choice1),.allocated(renamed_dst),.tag_a(renamed_src_a),.tag_b(renamed_src_b),
        .stale(renamed_stale),.ready_a(renamed_src_a_ready),.ready_b(renamed_src_b_ready));
    integer i, j, ri, checkpoint_count, slots, free_left, cp_left, transfers;
    reg prefix;
    always @* begin
        ri=-1; checkpoint_count=0;
        for(i=0;i<ROB;i=i+1) if(i<count) begin
            if(q[i][BR] && !q[i][RS]) checkpoint_count=checkpoint_count+1;
            if(q[i][7:0]==resolve_id) ri=i;
        end
        dispatch_accept=0;
        slots=ROB-count; free_left=free_count; cp_left=4-checkpoint_count;
        prefix=!rst && downstream_ready && !(resolve_valid && resolve_recover);
        for(i=0;i<2;i=i+1) begin
            if(prefix && dispatch_valid[i] && slots>0 && (!effective[i] || dispatch_move[i] || free_left>0) &&
               (!dispatch_branch[i] || cp_left>0)) begin
                dispatch_accept[i]=1'b1; slots=slots-1;
                if(dispatch_branch[i]) cp_left=cp_left-1;
                if(effective[i] && !dispatch_move[i]) free_left=free_left-1;
            end else prefix=1'b0;
        end
        retire_valid=0; retire_id=0; retire_dst_we=0; retire_branch=0; retire_move=0;
        retire_arch_dst=0; retire_dst=0; retire_stale=0; prefix=!rst;
        for(i=0;i<2;i=i+1) begin
            if(prefix && i<count && q[i][DN] && (!q[i][MV] || !q[i][WE] || ready[q[i][NEW +: PW]]) && (!q[i][BR] || q[i][RS]) &&
               (!(resolve_valid && resolve_recover) || i<ri)) begin
                retire_valid[i]=1'b1;
                retire_id[i*8 +: 8]=q[i][7:0];
                retire_dst_we[i]=q[i][WE]; retire_branch[i]=q[i][BR]; retire_move[i]=q[i][MV];
                retire_arch_dst[i*3 +: 3]=q[i][AR +: 3];
                retire_dst[i*PW +: PW]=q[i][NEW +: PW];
                retire_stale[i*PW +: PW]=q[i][OLD +: PW];
            end else prefix=1'b0;
        end
    end
    integer ni, nj;
    always @* begin
        transfers=(retire_valid[0] && retire_ready[0])+(retire_valid[1] && retire_ready[1]);
        next_committed=committed;
        for(ni=0;ni<2;ni=ni+1) if(ni<transfers && q[ni][WE])
            next_committed[q[ni][AR +: 3]*PW +: PW]=q[ni][NEW +: PW];
        next_count=count-transfers;
        for(ni=0;ni<ROB;ni=ni+1) begin
            nq[ni]=0;
            if(ni<next_count) nq[ni]=q[ni+transfers];
        end
        if(resolve_valid) begin
            for(ni=0;ni<ROB;ni=ni+1) if(ni<next_count && nq[ni][7:0]==resolve_id) begin
                nq[ni][RS]=1'b1;
                if(resolve_recover) next_count=ni+1;
            end
        end
        for(nj=0;nj<2;nj=nj+1) if(complete_valid[nj]) begin
            for(ni=0;ni<ROB;ni=ni+1) if(ni<next_count && nq[ni][7:0]==complete_id[nj*8 +: 8] &&
                    nq[ni][NEW +: PW]==complete_dst[nj*PW +: PW]) nq[ni][DN]=1'b1;
        end
        for(ni=0;ni<2;ni=ni+1) if(dispatch_accept[ni]) begin
            nq[next_count]={dispatch_move[ni],!dispatch_branch[ni],1'b0,renamed_stale[ni*PW +: PW],
                renamed_dst[ni*PW +: PW],dispatch_branch[ni],effective[ni],
                dispatch_dst[ni*3 +: 3],dispatch_id[ni*8 +: 8]};
            next_count=next_count+1;
        end
    end
    integer k;
    always @(posedge clk) begin
        if(rst) begin
            count<=0;
            for(k=0;k<ROB;k=k+1) q[k]<=0;
            for(k=0;k<8;k=k+1) committed[k*PW +: PW]<=k;
        end else begin
            count<=next_count; committed<=next_committed;
            for(k=0;k<ROB;k=k+1) q[k]<=nq[k];
        end
    end
endmodule

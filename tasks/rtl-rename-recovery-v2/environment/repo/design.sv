// Original legacy controller: one non-speculative instruction in flight.
// Upgrade this working ordinary path to the complete public v2 contract.
module rename_recovery #(parameter integer PHYS=24, ROB=16, PW=$clog2(PHYS)) (
    input wire clk, rst, downstream_ready,
    input wire [1:0] dispatch_valid,
    input wire [15:0] dispatch_id,
    input wire [5:0] dispatch_src_a, dispatch_src_b, dispatch_dst,
    input wire [1:0] dispatch_dst_we, dispatch_branch, dispatch_move,
    output wire [1:0] dispatch_accept,
    output wire [2*PW-1:0] renamed_src_a, renamed_src_b,
    output wire [1:0] renamed_src_a_ready, renamed_src_b_ready,
    output wire [2*PW-1:0] renamed_dst, renamed_stale,
    input wire [1:0] complete_valid,
    input wire [15:0] complete_id,
    input wire [2*PW-1:0] complete_dst,
    input wire resolve_valid,
    input wire [7:0] resolve_id,
    input wire resolve_recover,
    input wire [1:0] retire_ready,
    output wire [1:0] retire_valid,
    output wire [15:0] retire_id,
    output wire [1:0] retire_dst_we, retire_branch, retire_move,
    output wire [5:0] retire_arch_dst,
    output wire [2*PW-1:0] retire_dst, retire_stale
);
    reg [8*PW-1:0] committed;
    reg occupied, completed;
    reg [7:0] pending_id;
    reg [2:0] pending_arch;
    reg pending_we;
    reg [PW-1:0] pending_dst, pending_stale;
    wire [PW-1:0] source_a, source_b, previous, choice;
    wire choice_valid;
    wire effective=dispatch_dst_we[0] && dispatch_dst[2:0]!=0;

    legacy_map_lookup #(.PW(PW)) lookup (
        .committed(committed), .source_a(dispatch_src_a[2:0]),
        .source_b(dispatch_src_b[2:0]), .destination(dispatch_dst[2:0]),
        .tag_a(source_a), .tag_b(source_b), .stale(previous));
    legacy_free_pick #(.PHYS(PHYS)) pool (
        .committed(committed), .pending_valid(occupied && pending_we),
        .pending_tag(pending_dst), .choice(choice), .available(choice_valid));

    assign dispatch_accept[0]=!rst && downstream_ready && !occupied &&
        dispatch_valid[0] && !dispatch_branch[0] && !dispatch_move[0] &&
        !(resolve_valid && resolve_recover) && (!effective || choice_valid);
    assign dispatch_accept[1]=1'b0;
    assign renamed_src_a={{PW{1'b0}},source_a};
    assign renamed_src_b={{PW{1'b0}},source_b};
    assign renamed_src_a_ready=2'b01;
    assign renamed_src_b_ready=2'b01;
    assign renamed_dst={{PW{1'b0}},(effective ? choice : {PW{1'b0}})};
    assign renamed_stale={{PW{1'b0}},(effective ? previous : {PW{1'b0}})};

    assign retire_valid={1'b0,(!rst && occupied && completed)};
    assign retire_id={8'b0,pending_id};
    assign retire_dst_we={1'b0,pending_we};
    assign retire_branch=0;
    assign retire_move=0;
    assign retire_arch_dst={3'b0,pending_arch};
    assign retire_dst={{PW{1'b0}},pending_dst};
    assign retire_stale={{PW{1'b0}},pending_stale};

    integer a, port;
    always @(posedge clk) begin
        if(rst) begin
            for(a=0;a<8;a=a+1) committed[a*PW +: PW]<=a;
            occupied<=0;completed<=0;pending_id<=0;pending_arch<=0;
            pending_we<=0;pending_dst<=0;pending_stale<=0;
        end else begin
            if(retire_valid[0] && retire_ready[0]) begin
                occupied<=0;
                if(pending_we) committed[pending_arch*PW +: PW]<=pending_dst;
            end
            for(port=0;port<2;port=port+1)
                if(occupied && complete_valid[port] &&
                   complete_id[port*8 +: 8]==pending_id &&
                   complete_dst[port*PW +: PW]==pending_dst) completed<=1;
            if(dispatch_accept[0]) begin
                occupied<=1;completed<=0;
                pending_id<=dispatch_id[7:0];pending_arch<=dispatch_dst[2:0];
                pending_we<=effective;
                pending_dst<=renamed_dst[0 +: PW];
                pending_stale<=renamed_stale[0 +: PW];
            end
        end
    end
endmodule

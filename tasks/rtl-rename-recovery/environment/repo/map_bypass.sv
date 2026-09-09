// Original repair starter: audit interactions across map, ownership and recovery.
module rename_map #(parameter PHYS=24, ROB=16, PW=$clog2(PHYS)) (
    input wire [8*PW-1:0] committed,
    input wire [31:0] count,
    input wire [ROB-1:0] has_dst,
    input wire [ROB*3-1:0] arch,
    input wire [ROB*PW-1:0] dst,
    input wire [PHYS-1:0] ready,
    input wire [1:0] accept, effective,
    input wire [5:0] src_a, src_b, new_arch,
    input wire [2*PW-1:0] allocated,
    output reg [2*PW-1:0] tag_a, tag_b, stale,
    output reg [1:0] ready_a, ready_b
);
    reg [8*PW-1:0] map;
    reg [PHYS-1:0] avail;
    integer i;
    always @* begin
        map=committed; avail=ready;
        tag_a=0; tag_b=0; stale=0; ready_a=0; ready_b=0;
        for (i=0;i<ROB;i=i+1) if (i<count && has_dst[i])
            map[arch[i*3 +: 3]*PW +: PW]=dst[i*PW +: PW];
        for (i=0;i<2;i=i+1) if (accept[i]) begin
            tag_a[i*PW +: PW]=map[src_a[i*3 +: 3]*PW +: PW];
            tag_b[i*PW +: PW]=map[src_b[i*3 +: 3]*PW +: PW];
            ready_a[i]=avail[tag_a[i*PW +: PW]];
            ready_b[i]=avail[tag_b[i*PW +: PW]];
            if (effective[i]) begin
                stale[i*PW +: PW]=map[new_arch[i*3 +: 3]*PW +: PW];
                if (i==1) map[new_arch[i*3 +: 3]*PW +: PW]=allocated[i*PW +: PW];
                avail[allocated[i*PW +: PW]]=1'b0;
            end
        end
    end
endmodule

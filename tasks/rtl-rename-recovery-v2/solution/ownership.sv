module rename_ownership #(parameter PHYS=24, ROB=16, PW=$clog2(PHYS)) (
    input wire [8*PW-1:0] committed,
    input wire [31:0] count,
    input wire [ROB-1:0] has_dst, done, is_move,
    input wire [ROB*PW-1:0] dst,
    output reg [PHYS-1:0] owned, ready,
    output reg [31:0] free_count,
    output reg [PW-1:0] choice0, choice1
);
    integer i, found;
    always @* begin
        owned=0; ready=0; free_count=0; choice0=0; choice1=0; found=0;
        for (i=0;i<8;i=i+1) begin
            owned[committed[i*PW +: PW]]=1'b1;
            ready[committed[i*PW +: PW]]=1'b1;
        end
        for (i=0;i<ROB;i=i+1) if (i<count && has_dst[i]) begin
            owned[dst[i*PW +: PW]]=1'b1;
            if (!is_move[i]) ready[dst[i*PW +: PW]]=done[i];
        end
        owned[0]=1'b1; ready[0]=1'b1;
        for (i=1;i<PHYS;i=i+1) if (!owned[i]) begin
            if (found==0) choice0=i;
            if (found==1) choice1=i;
            found=found+1;
            free_count=free_count+1;
        end
    end
endmodule

// Single-choice pool for the original one-inflight controller.
module legacy_free_pick #(parameter PHYS=24, PW=$clog2(PHYS)) (
    input wire [8*PW-1:0] committed,
    input wire pending_valid,
    input wire [PW-1:0] pending_tag,
    output reg [PW-1:0] choice,
    output reg available
);
    reg [PHYS-1:0] reserved;
    integer a,p;
    always @* begin
        reserved=0;reserved[0]=1'b1;choice=0;available=0;
        for(a=0;a<8;a=a+1) reserved[committed[a*PW +: PW]]=1'b1;
        if(pending_valid) reserved[pending_tag]=1'b1;
        for(p=1;p<PHYS;p=p+1) if(!reserved[p] && !available) begin
            choice=p;available=1'b1;
        end
    end
endmodule

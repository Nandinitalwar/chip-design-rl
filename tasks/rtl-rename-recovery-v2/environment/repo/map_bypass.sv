// Legacy ordinary issue occurs only after the previous instruction retires.
module legacy_map_lookup #(parameter PW=5) (
    input wire [8*PW-1:0] committed,
    input wire [2:0] source_a, source_b, destination,
    output wire [PW-1:0] tag_a, tag_b, stale
);
    assign tag_a=committed[source_a*PW +: PW];
    assign tag_b=committed[source_b*PW +: PW];
    assign stale=committed[destination*PW +: PW];
endmodule

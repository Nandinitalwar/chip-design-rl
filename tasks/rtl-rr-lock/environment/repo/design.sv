module rr_lock #(parameter N=4)(
 input wire clk, input wire rst, input wire [N-1:0] req,
 input wire [N-1:0] lock, output reg [N-1:0] grant
);
always @* grant = req & {N{1'b0}};
endmodule

module skid_flush #(parameter WIDTH=16)(
 input wire clk, input wire rst, input wire flush,
 input wire in_valid, output wire in_ready, input wire [WIDTH-1:0] in_data,
 output wire out_valid, input wire out_ready, output wire [WIDTH-1:0] out_data
);
assign in_ready=0; assign out_valid=0; assign out_data=0;
endmodule

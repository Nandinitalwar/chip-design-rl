module skid_flush #(parameter WIDTH=16)(
 input wire clk, input wire rst, input wire flush,
 input wire in_valid, output wire in_ready, input wire [WIDTH-1:0] in_data,
 output wire out_valid, input wire out_ready, output wire [WIDTH-1:0] out_data
);
reg [WIDTH-1:0] q0,q1;
reg [1:0] count;
assign out_valid = !rst && !flush && count != 0;
assign in_ready = !rst && !flush && (count < 2 || out_ready);
assign out_data = q0;
wire push = in_valid && in_ready;
wire pop = out_valid && out_ready;
always @(posedge clk) begin
 if (rst || flush) begin count<=0; q0<=0; q1<=0; end
 else begin
  case ({push,pop})
   2'b10: begin if(count==0) q0<=in_data; else q1<=in_data; count<=count+1; end
   2'b01: begin q0<=q1; count<=count-1; end
   2'b11: begin if(count==1) q0<=in_data; else begin q0<=q1; q1<=in_data; end end
  endcase
 end
end
endmodule

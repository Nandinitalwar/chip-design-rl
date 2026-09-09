module rr_lock #(parameter N=4)(
 input wire clk, input wire rst, input wire [N-1:0] req,
 input wire [N-1:0] lock, output reg [N-1:0] grant
);
integer ptr,owner,choice,j,idx;
reg held;
always @* begin
 grant={N{1'b0}};choice=-1;
 if(!rst) begin
  if(held) begin grant[owner]=1'b1;choice=owner;end
  else begin
   for(j=0;j<N;j=j+1) begin
    idx=(ptr+j)%N;
    if(choice==-1 && req[idx]) choice=idx;
   end
   if(choice!=-1) grant[choice]=1'b1;
  end
 end
end
always @(posedge clk) begin
 if(rst) begin ptr<=0;owner<=0;held<=0;end
 else if(held) begin
  if(!lock[owner]) begin held<=0;ptr<=(owner+1)%N;end
 end else if(choice!=-1) begin
  if(lock[choice]) begin held<=1;owner<=choice;end
  else ptr<=(choice+1)%N;
 end
end
endmodule

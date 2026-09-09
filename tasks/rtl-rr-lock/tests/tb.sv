module arb_checker #(parameter N=4)(output reg done=0);
reg clk=0; always #5 clk=~clk;
reg rst=1;reg [N-1:0] req=0,lock=0;wire [N-1:0] grant;
rr_lock #(.N(N)) dut(clk,rst,req,lock,grant);
integer ptr=0,own=0,chosen,j,i,k,step=0;reg held=0;
reg [N-1:0] expected,mask;reg [31:0] rng=32'h93ef041b;
function [31:0] advance(input [31:0] x);begin advance=(x<<1)^({32{x[31]}}&32'h04c11db7);end endfunction
task cycle(input rr,input [N-1:0] requests,input [N-1:0] locks);
begin
 @(negedge clk);rst=rr;req=requests;lock=locks;
 expected=0;chosen=-1;
 if(!rr) begin
  if(held) chosen=own;
  else for(j=0;j<N;j=j+1) if(chosen<0 && requests[(ptr+j)%N]) chosen=(ptr+j)%N;
  if(chosen>=0) expected[chosen]=1;
 end
 #1;if(grant !== expected) $fatal(1,"N=%0d step=%0d expected=%b got=%b",N,step,expected,grant);
 @(posedge clk);
 if(rr) begin ptr=0;own=0;held=0;end
 else if(held) begin if(!locks[own]) begin held=0;ptr=(own+1)%N;end end
 else if(chosen>=0) begin
  if(locks[chosen]) begin held=1;own=chosen;end
  else ptr=(chosen+1)%N;
 end
 step=step+1;
end endtask
initial begin
 cycle(1,{N{1'b1}},0);
 for(i=0;i<3*N;i=i+1) cycle(0,{N{1'b1}},0);
 cycle(0,0,0);cycle(0,{N{1'b1}},0);
 for(k=0;k<N;k=k+1) begin
  cycle(1,0,0);mask=0;mask[k]=1;
  cycle(0,mask,mask);
  cycle(0,0,mask);cycle(0,{N{1'b1}},mask);
  cycle(0,{N{1'b1}},0);cycle(0,{N{1'b1}},0);
 end
 cycle(1,0,0);
 for(i=0;i<1800;i=i+1) begin
  rng=advance(rng);cycle(i%149==0,rng[N-1:0],rng[16+:N]);
 end
 cycle(1,0,0);
 for(i=0;i<10*N;i=i+1) cycle(0,{N{1'b1}},0);
 done=1;
end
endmodule
module tb;
wire a,b,c;
arb_checker #(.N(1)) c1(a);arb_checker #(.N(3)) c3(b);arb_checker #(.N(4)) c4(c);
initial begin wait(a&&b&&c);$display("ALL_TESTS_PASSED");$finish;end
initial begin #100000;$fatal(1,"timeout");end
endmodule

module skid_checker #(parameter WIDTH=16)(output reg done=0);
reg clk=0; always #5 clk=~clk;
reg rst=1,flush=0,iv=0,ordy=0;
reg [WIDTH-1:0] din=0;
wire ir,ov; wire [WIDTH-1:0] dout;
skid_flush #(.WIDTH(WIDTH)) dut(clk,rst,flush,iv,ir,din,ov,ordy,dout);
integer n=0,step=0,i,bitidx; reg [WIDTH-1:0] random_word; reg [WIDTH-1:0] model[0:1];
reg er,ev,push,pop; reg [31:0] rng=32'hb3e92157;
function [31:0] advance(input [31:0] x); begin advance=(x<<1)^{32{ x[31] }}&32'h04c11db7; end endfunction
task cycle(input rr,input ff,input vv,input ready,input [WIDTH-1:0] data);
begin
 @(negedge clk); rst=rr;flush=ff;iv=vv;ordy=ready;din=data;
 #1; er= !rr && !ff && (n<2 || ready); ev= !rr && !ff && n!=0;
 if(ir !== er || ov !== ev) $fatal(1,"handshake mismatch step=%0d n=%0d",step,n);
 if(ev && dout !== model[0]) $fatal(1,"data mismatch step=%0d got=%h expected=%h",step,dout,model[0]);
 push=vv&&er;pop=ready&&ev;
 @(posedge clk);
 if(rr||ff) n=0;
 else begin
  if(pop) begin model[0]=model[1]; n=n-1; end
  if(push) begin model[n]=data;n=n+1;end
 end
 step=step+1;
end endtask
initial begin
 cycle(1,0,1,1,16'hffff);
 cycle(0,0,1,0,16'h1111);cycle(0,0,1,0,16'h2222);
 cycle(0,0,1,0,16'h3333);cycle(0,0,1,1,16'h4444);
 cycle(0,0,0,1,0);cycle(0,0,0,1,0);
 cycle(0,0,1,1,16'ha001);cycle(0,0,1,1,16'ha002);
 cycle(0,1,1,1,16'hdead);cycle(0,0,0,1,0);
 for(i=0;i<2500;i=i+1) begin
  for(bitidx=0;bitidx<WIDTH;bitidx=bitidx+1) begin
   rng=advance(rng); random_word[bitidx]=rng[0];
  end
  rng=advance(rng);
  cycle(i%137==0,i%29==0,rng[0],rng[6],random_word);
 end
 cycle(0,0,0,1,0);cycle(0,0,0,1,0);cycle(0,0,0,1,0);
 done=1;
end
endmodule

module tb;
wire a,b,c,d,e,f;
skid_checker #(.WIDTH(1)) c1(a);
skid_checker #(.WIDTH(9)) c9(b);
skid_checker #(.WIDTH(16)) c16(c);
skid_checker #(.WIDTH(17)) c17(d);
skid_checker #(.WIDTH(32)) c32(e);
skid_checker #(.WIDTH(65)) c65(f);
initial begin wait(a&&b&&c&&d&&e&&f);$display("ALL_TESTS_PASSED");$finish;end
initial begin #100000;$fatal(1,"timeout");end
endmodule

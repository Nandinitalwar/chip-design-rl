"""Trusted port serializer; observations are data, never executable code or reward."""
import selectors
import subprocess


def ports(pw):
    inputs=[('rst',1),('downstream_ready',1),('dispatch_valid',2),('dispatch_id',16),
            ('dispatch_src_a',6),('dispatch_src_b',6),('dispatch_dst',6),('dispatch_dst_we',2),
            ('dispatch_branch',2),('dispatch_move',2),('complete_valid',2),('complete_id',16),('complete_dst',2*pw),
            ('resolve_valid',1),('resolve_id',8),('resolve_recover',1),('retire_ready',2)]
    outputs=[('dispatch_accept',2),('renamed_src_a',2*pw),('renamed_src_b',2*pw),
             ('renamed_src_a_ready',2),('renamed_src_b_ready',2),('renamed_dst',2*pw),
             ('renamed_stale',2*pw),('retire_valid',2),('retire_id',16),('retire_dst_we',2),
             ('retire_branch',2),('retire_move',2),('retire_arch_dst',6),('retire_dst',2*pw),('retire_stale',2*pw)]
    return inputs,outputs


def testbench(pw):
    ins,outs=ports(pw)
    lines=['module tb; reg clk=0;']
    for name,w in ins:
        lines.append(f'reg [{w-1}:0] {name}=0;')
    for name,w in outs:
        lines.append(f'wire [{w-1}:0] {name};')
    lines+=['rename_recovery dut(.*);',f'reg [{sum(w for _,w in ins)-1}:0] stimulus;',
            'reg [4095:0] line; integer scan; initial begin', 'while (1) begin',
            'scan=$fgets(line,32\'h80000000);', 'if(scan==0) $finish;', 'scan=$sscanf(line,"%h",stimulus);',
            'if(scan!=1) $finish;',
            '{'+','.join(n for n,_ in reversed(ins))+'}=stimulus;',
            '#2;', '$display("%b",{'+','.join(n for n,_ in reversed(outs))+'});',
            "$fflush(32'h80000001);", '#1; clk=1; #2; clk=0; #1;', 'end end endmodule']
    return '\n'.join(lines)+'\n'


class Observation:
    def __init__(self,text,pw):
        _,fields=ports(pw)
        width=sum(w for _,w in fields)
        if len(text)!=width or any(c not in '01xz' for c in text.lower()):
            raise ValueError('invalid bit-preserving observation: '+repr(text))
        binary=text.lower()[::-1]
        self.bits={}; offset=0
        for n,w in fields:
            self.bits[n]=binary[offset:offset+w]
            offset+=w
    def get(self,name,lane=0,width=None):
        bits=self.bits[name]
        width=width or len(bits)
        field=bits[lane*width:(lane+1)*width][::-1]
        return None if any(c in 'xz' for c in field) else int(field,2)


class Simulator:
    def __init__(self,command,pw,cwd,drop=None):
        self.pw=pw
        self.proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                   text=True,bufsize=1,cwd=cwd,preexec_fn=drop)
        self.selector=selectors.DefaultSelector()
        self.selector.register(self.proc.stdout,selectors.EVENT_READ)
        self.lines=[]
    def exchange(self,values):
        word=0; shift=0
        for n,w in ports(self.pw)[0]:
            value=values.get(n,0)
            assert 0<=value<(1<<w), (n,value,w)
            word |= value<<shift; shift+=w
        self.proc.stdin.write(f'{word:x}\n'); self.proc.stdin.flush()
        if not self.selector.select(30):
            raise TimeoutError('candidate simulation observation timeout')
        line=self.proc.stdout.readline().strip()
        self.lines.append({'input':f'{word:x}','output':line})
        return Observation(line,self.pw)
    def close(self):
        self.selector.close()
        self.exit_before_close=self.proc.poll()
        if self.exit_before_close is None:
            self.proc.kill()
        _,self.stderr_text=self.proc.communicate(timeout=10)

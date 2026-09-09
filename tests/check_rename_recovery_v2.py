"""Author-only deterministic validation. No model trials, commits or old-task edits.
Run: python3 -u tests/check_rename_recovery_v2.py --image chip-rl-rename-recovery-v2:author-review
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'tasks/rtl-rename-recovery-v2'
NAMES=('design.sv','map_bypass.sv','ownership.sv')


def snapshot_leak(source):
    """Retain checkpoint-time owned bits which become free before rollback.
    This isolates the documented snapshot free-list leak, while preserving safety.
    """
    s=source.replace('wire [31:0] free_count;', 'wire [31:0] raw_free_count; reg [31:0] free_count;')
    s=s.replace('wire [PW-1:0] choice0, choice1;', 'wire [PW-1:0] raw_choice0, raw_choice1; reg [PW-1:0] choice0, choice1;')
    s=s.replace('.free_count(free_count),.choice0(choice0),.choice1(choice1)', '.free_count(raw_free_count),.choice0(raw_choice0),.choice1(raw_choice1)')
    extra='''    reg [PHYS-1:0] blocked;
    reg [PHYS-1:0] snap[0:ROB-1], nsnap[0:ROB-1];
    reg [PHYS-1:0] surviving_owned;
    integer sf, sk, found_free, sn, base;
    always @* begin
        free_count=0; choice0=0; choice1=0; found_free=0;
        for(sf=1;sf<PHYS;sf=sf+1) if(!owned[sf] && !blocked[sf]) begin
            if(found_free==0) choice0=sf;
            if(found_free==1) choice1=sf;
            found_free=found_free+1;free_count=free_count+1;
        end
    end
    always @* begin
        for(sn=0;sn<ROB;sn=sn+1) begin
            nsnap[sn]=0;
            if(sn<count-transfers) nsnap[sn]=snap[sn+transfers];
        end
        base=next_count-dispatch_accept[0]-dispatch_accept[1];
        if(dispatch_accept[0] && dispatch_branch[0]) nsnap[base]=owned;
        if(dispatch_accept[1] && dispatch_branch[1]) begin
            nsnap[base+1]=owned;
            if(effective[0]) nsnap[base+1][renamed_dst[0 +: PW]]=1'b1;
        end
        surviving_owned=0;
        for(sn=0;sn<8;sn=sn+1) surviving_owned[next_committed[sn*PW +: PW]]=1'b1;
        for(sn=0;sn<ROB;sn=sn+1) if(sn<next_count && nq[sn][WE])
            surviving_owned[nq[sn][NEW +: PW]]=1'b1;
    end
    always @(posedge clk) begin
        if(rst) begin
            blocked<=0;
            for(sk=0;sk<ROB;sk=sk+1) snap[sk]<=0;
        end else begin
            for(sk=0;sk<ROB;sk=sk+1) snap[sk]<=nsnap[sk];
            if(resolve_valid && resolve_recover && ri>=0)
                blocked<=blocked | (snap[ri] & ~surviving_owned);
        end
    end
'''
    return s.replace('    integer k;',extra+'    integer k;')


def incremental_alternative(oracle):
    """Alternative physical-ready registers and per-tag reference counting."""
    result=dict(oracle)
    s=result['design.sv'].replace('.owned(owned),.ready(ready),', '.owned(owned),.ready(unused_ready),')
    s=s.replace('wire [PHYS-1:0] owned, ready;', 'wire [PHYS-1:0] owned, ready, unused_ready;\n    reg [PHYS-1:0] physical_ready;\n    assign ready=physical_ready;')
    extra="""    integer rp, rr;
    always @(posedge clk) begin
        if(rst) physical_ready<={PHYS{1'b1}};
        else begin
            for(rp=0;rp<2;rp=rp+1) if(complete_valid[rp])
                for(rr=0;rr<ROB;rr=rr+1)
                    if(rr<count && q[rr][WE] && !q[rr][MV] &&
                       q[rr][7:0]==complete_id[rp*8 +: 8] && q[rr][NEW +: PW]==complete_dst[rp*PW +: PW] &&
                       (!(resolve_valid && resolve_recover) || rr<=ri)) physical_ready[q[rr][NEW +: PW]]<=1'b1;
            for(rp=0;rp<2;rp=rp+1)
                if(dispatch_accept[rp] && effective[rp] && !dispatch_move[rp]) physical_ready[renamed_dst[rp*PW +: PW]]<=1'b0;
        end
    end
"""
    result['design.sv']=s.replace('    integer k;',extra+'    integer k;')
    result['ownership.sv']="""module rename_ownership #(parameter PHYS=24, ROB=16, PW=$clog2(PHYS)) (
    input wire [8*PW-1:0] committed,
    input wire [31:0] count,
    input wire [ROB-1:0] has_dst, done, is_move,
    input wire [ROB*PW-1:0] dst,
    output reg [PHYS-1:0] owned, ready,
    output reg [31:0] free_count,
    output reg [PW-1:0] choice0, choice1
);
    integer p,a,r,refs,found;
    always @* begin
        owned=0;ready=0;free_count=0;choice0=0;choice1=0;found=0;refs=0;
        for(p=0;p<PHYS;p=p+1) begin
            refs=0;
            for(a=0;a<8;a=a+1) if(committed[a*PW +: PW]==p) refs=refs+1;
            for(r=0;r<ROB;r=r+1) if(r<count && has_dst[r] && dst[r*PW +: PW]==p) refs=refs+1;
            owned[p]=(refs!=0 || p==0);
        end
        for(p=PHYS-1;p>=1;p=p-1) if(!owned[p]) begin
            if(found==0) choice0=p;
            if(found==1) choice1=p;
            found=found+1;free_count=free_count+1;
        end
    end
endmodule
"""
    return result


def unsafe_reclaim(oracle,on_kill):
    """Model freeing a stale/killed tag without checking its other owners."""
    result=dict(oracle)
    s=result['ownership.sv'].replace('input wire [8*PW-1:0] committed,','input wire [8*PW-1:0] committed,\n    input wire [PHYS-1:0] reclaimed,')
    result['ownership.sv']=s.replace('if (!owned[i]) begin','if (!owned[i] || reclaimed[i]) begin')
    s=result['design.sv'].replace('wire [PHYS-1:0] owned, ready;', 'wire [PHYS-1:0] owned, ready;\n    reg [PHYS-1:0] reclaimed;')
    s=s.replace('.owned(owned),.ready(ready),', '.owned(owned),.ready(ready),.reclaimed(reclaimed),')
    set_bits="""            for(cr=0;cr<2;cr=cr+1)
                if(retire_valid[cr] && retire_ready[cr] && retire_dst_we[cr]) reclaimed[retire_stale[cr*PW +: PW]]<=1'b1;
"""
    if on_kill:
        set_bits="""            if(resolve_valid && resolve_recover)
                for(cr=0;cr<ROB;cr=cr+1)
                    if(cr<count && cr>ri && q[cr][WE] && q[cr][MV]) reclaimed[q[cr][NEW +: PW]]<=1'b1;
"""
    extra="""    integer cr;
    always @(posedge clk) begin
        if(rst) reclaimed<=0;
        else begin
"""+set_bits+"""            for(cr=0;cr<2;cr=cr+1)
                if(dispatch_accept[cr] && effective[cr] && !dispatch_move[cr]) reclaimed[renamed_dst[cr*PW +: PW]]<=1'b0;
        end
    end
"""
    result['design.sv']=s.replace('    integer k;',extra+'    integer k;')
    return result


def variants():
    oracle={n:(TASK/'solution'/n).read_text() for n in NAMES}
    cases={'oracle':oracle,'descending-allocator':dict(oracle),
           'starter':{n:(TASK/'environment/repo'/n).read_text() for n in NAMES}}
    cases['descending-allocator']['ownership.sv']=oracle['ownership.sv'].replace('for (i=1;i<PHYS;i=i+1)', 'for (i=PHYS-1;i>=1;i=i-1)')
    cases['invalid-lane-unknowns']=dict(oracle)
    unknown=oracle['map_bypass.sv'].replace('allocated=0; allocated_count=0;', "allocated={2*PW{1'bx}}; allocated_count=0;")
    assert unknown!=oracle['map_bypass.sv']
    cases['invalid-lane-unknowns']['map_bypass.sv']=unknown
    cases['incremental-ready-refcounts']=incremental_alternative(oracle)
    mutations={
        'port1-requires-port0':('design.sv','if(complete_valid[nj])','if(complete_valid[nj] && (nj==0 || complete_valid[0]))'),
        'missing-lane-bypass':('map_bypass.sv','                map[new_arch[i*3 +: 3]*PW +: PW]=allocated[i*PW +: PW];','                if(i==1) map[new_arch[i*3 +: 3]*PW +: PW]=allocated[i*PW +: PW];'),
        'inclusive-branch-kill':('design.sv','if(resolve_recover) next_count=ni+1;','if(resolve_recover) next_count=ni;'),
        'lost-commit-on-recovery':('design.sv','        next_count=count-transfers;','        if(resolve_valid && resolve_recover) next_committed=committed;\n        next_count=count-transfers;'),
        'physical-tag-only-completion':('design.sv','nq[ni][7:0]==complete_id[nj*8 +: 8] &&',"1'b1 &&"),
        'premature-pending-free':('ownership.sv','i<count && has_dst[i]','i<count && has_dst[i] && done[i]'),
        'permanent-single-lane':('design.sv','prefix && dispatch_valid[i] && slots>0','prefix && i==0 && dispatch_valid[i] && slots>0'),
        'ignore-correct-resolution':('design.sv',"nq[ni][RS]=1'b1;","if(resolve_recover) nq[ni][RS]=1'b1;"),
        'retire-unresolved-branch':('design.sv','(!q[i][BR] || q[i][RS])',"1'b1"),
        'incorrect-zero-dest-metadata':('design.sv','retire_arch_dst[i*3 +: 3]=q[i][AR +: 3];','retire_arch_dst[i*3 +: 3]=q[i][WE] ? q[i][AR +: 3] : 0;'),
    }
    mutations.update({
        'move-allocates-new-tag':('map_bypass.sv','if (move[i]) allocated[i*PW +: PW]=tag_a[i*PW +: PW];',"if (1'b0) allocated[i*PW +: PW]=tag_a[i*PW +: PW];"),
        'move-clears-ready':('map_bypass.sv',"if (!move[i]) avail[allocated[i*PW +: PW]]=1'b0;","avail[allocated[i*PW +: PW]]=1'b0;"),
        'alias-done-overwrites-producer-ready':('ownership.sv','if (!is_move[i]) ready[dst[i*PW +: PW]]=done[i];','ready[dst[i*PW +: PW]]=done[i];'),
        'move-requires-free-register':('design.sv','(!effective[i] || dispatch_move[i] || free_left>0)','(!effective[i] || free_left>0)'),
        'zero-source-move-metadata':('map_bypass.sv','if (move[i]) allocated[i*PW +: PW]=tag_a[i*PW +: PW];','if (move[i]) allocated[i*PW +: PW]=(tag_a[i*PW +: PW]==0 ? choice0 : tag_a[i*PW +: PW]);'),
        'drop-retirement-move-kind':('design.sv','retire_move[i]=q[i][MV];',"retire_move[i]=1'b0;"),
    })
    for label,(name,old,new) in mutations.items():
        assert old in oracle[name],label
        cases[label]=dict(oracle);cases[label][name]=oracle[name].replace(old,new)
    cases['snapshot-free-list-leak']=dict(oracle)
    cases['snapshot-free-list-leak']['design.sv']=snapshot_leak(oracle['design.sv'])
    numeric=oracle['design.sv'].replace('integer ni, nj;', 'integer ni, nj, age_count, age_index;')
    numeric=numeric.replace('        transfers=', '        age_count=0; age_index=0;\n        transfers=')
    numeric=numeric.replace('if(resolve_recover) next_count=ni+1;', '''if(resolve_recover) begin
                    age_count=0;
                    for(age_index=0;age_index<ROB;age_index=age_index+1)
                        if(age_index<count-transfers && nq[age_index][7:0]<=resolve_id) age_count=age_count+1;
                    next_count=age_count;
                end''')
    cases['numeric-token-age']=dict(oracle);cases['numeric-token-age']['design.sv']=numeric
    cases['unconditional-stale-reclaim']=unsafe_reclaim(oracle,False)
    cases['killed-alias-reclaim']=unsafe_reclaim(oracle,True)
    return cases


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--image',default='chip-rl-rename-recovery-v2:author-review')
    ap.add_argument('--output',type=Path,default=ROOT/'work/rename-v2-validation')
    ap.add_argument('--case',action='append')
    args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    results=[]
    for name,sources in variants().items():
        if args.case and name not in args.case:continue
        case=args.output/name;case.mkdir(exist_ok=True)
        for filename,source in sources.items(): (case/filename).write_text(source)
        command=['docker','run','--rm','--network','none','--cpus','1','--memory','2g',
                 '-v',f'{TASK / "tests"}:/root/private-tests:ro','-v',f'{case.resolve()}:/candidate',
                 '-e','TASK_WORKSPACE=/candidate','-e','VERIFIER_LOG_DIR=/candidate/logs',
                 args.image,'bash','/root/private-tests/test.sh']
        proc=subprocess.run(command,text=True,capture_output=True,timeout=1800)
        (case/'runner.log').write_text(proc.stdout+proc.stderr)
        status=json.loads((case/'logs/status.json').read_text())
        assert proc.returncode==0,(name,proc.returncode,status)
        reward=int((case/'logs/reward.txt').read_text())
        expected=int(name in ('oracle','descending-allocator','invalid-lane-unknowns','incremental-ready-refcounts'))
        assert reward==expected,(name,reward,expected,status)
        expected_status='functional_and_synthesis_pass' if expected else 'functional_failure'
        assert status['classification']==expected_status,(name,status)
        if not expected: assert status['last_label']!='seeded-stress',(name,status)
        result={'case':name,'reward':reward,'status':status,'source_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in sources.items()}}
        if expected:result['coverage']=json.loads((case/'logs/coverage.json').read_text())
        results.append(result)
        print(name,reward,status.get('last_label','all six configurations'),flush=True)
        (args.output/'partial.json').write_text(json.dumps(results,indent=2)+'\n')
    image=json.loads(subprocess.check_output(['docker','image','inspect',args.image]))[0]
    summary={'task':'rtl-rename-recovery-v2','status':'author-validation','difficulty':'uncalibrated',
             'target_success_rate':0.2,'model_trials_run':0,'image_id':image['Id'], 'results':results}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Saved',args.output/'summary.json',flush=True)

if __name__=='__main__':main()

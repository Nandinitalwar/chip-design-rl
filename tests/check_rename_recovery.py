"""Author-only deterministic validation. No model trials, commits or old-task edits.
Run: python3 -u tests/check_rename_recovery.py --image chip-rl-rename-recovery:author-review
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
TASK=ROOT/'tasks/rtl-rename-recovery'
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


def variants():
    oracle={n:(TASK/'solution'/n).read_text() for n in NAMES}
    cases={'oracle':oracle,'descending-allocator':dict(oracle),
           'starter':{n:(TASK/'environment/repo'/n).read_text() for n in NAMES}}
    cases['descending-allocator']['ownership.sv']=oracle['ownership.sv'].replace('for (i=1;i<PHYS;i=i+1)', 'for (i=PHYS-1;i>=1;i=i-1)')
    cases['invalid-lane-unknowns']=dict(oracle)
    unknown=oracle['design.sv'].replace('dispatch_accept=0; renamed_dst=0;', "dispatch_accept=0; renamed_dst={2*PW{1'bx}};")
    unknown=unknown.replace("dispatch_accept[i]=1'b1; slots=slots-1;", "dispatch_accept[i]=1'b1; slots=slots-1; renamed_dst[i*PW +: PW]=0;")
    cases['invalid-lane-unknowns']['design.sv']=unknown
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
    return cases


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--image',default='chip-rl-rename-recovery:author-review')
    ap.add_argument('--output',type=Path,default=ROOT/'work/rename-validation')
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
        expected=int(name in ('oracle','descending-allocator','invalid-lane-unknowns'))
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
    summary={'task':'rtl-rename-recovery','status':'author-validation','difficulty':'uncalibrated',
             'target_success_rate':0.2,'model_trials_run':0,'image_id':image['Id'], 'results':results}
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print('Saved',args.output/'summary.json',flush=True)

if __name__=='__main__':main()

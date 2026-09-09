"""Bounded grading-boundary controls; not a general container security audit."""
import argparse
import json
from pathlib import Path
import subprocess
from check_rename_recovery_v2 import ROOT,TASK,NAMES


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--image',default='chip-rl-rename-recovery-v2:author-review')
    args=ap.parse_args();out=ROOT/'work/rename-v2-isolation';out.mkdir(parents=True,exist_ok=True)
    results=[]
    snippets={
        'blackbox-top':None,
        'forged-success-marker':'initial $display("ALL_TESTS_PASSED functional_and_synthesis_pass reward=1");',
        'attempt-reward-write':'integer f; initial begin f=$fopen("/candidate/logs/reward.txt","w"); $fdisplay(f,"1"); $fclose(f); end',
    }
    for name,snippet in snippets.items():
        case=out/name;case.mkdir(exist_ok=True)
        for filename in NAMES:
            source=(TASK/'environment/repo'/filename).read_text()
            if filename=='design.sv':
                if name=='blackbox-top':
                    source=source[:source.index('    reg [8*PW-1:0] committed;')]+'endmodule\n'
                    source=source.replace('module rename_recovery','(* blackbox *) module rename_recovery')
                else: source=source.replace('endmodule',snippet+'\nendmodule')
            (case/filename).write_text(source)
        command=['docker','run','--rm','--network','none','--cpus','1','--memory','2g',
                 '-v',f'{TASK/"tests"}:/root/private-tests:ro','-v',f'{case}:/candidate',
                 '-e','TASK_WORKSPACE=/candidate','-e','VERIFIER_LOG_DIR=/candidate/logs',
                 args.image,'bash','/root/private-tests/test.sh']
        p=subprocess.run(command,text=True,capture_output=True,timeout=300)
        assert p.returncode==0,(name,p.stdout,p.stderr)
        status=json.loads((case/'logs/status.json').read_text())
        assert (case/'logs/reward.txt').read_text().strip()=='0',name
        expected='functional_failure' if name=='forged-success-marker' else 'candidate_synthesis_failure'
        assert status['classification']==expected,(name,status)
        results.append({'case':name,'reward':0,'status':status})
    missing=out/'missing-tools';missing.mkdir(exist_ok=True)
    p=subprocess.run(['docker','run','--rm','--network','none','-v',f'{TASK / "tests"}:/root/private-tests:ro','-v',f'{missing}:/candidate','-e','VERIFIER_LOG_DIR=/candidate/logs','-e','PATH=/missing-tools','--entrypoint','/usr/bin/python3',args.image,'/root/private-tests/grader.py'],text=True,capture_output=True,timeout=30)
    (missing/'runner.log').write_text(p.stdout+p.stderr)
    missing_status=json.loads((missing/'logs/status.json').read_text())
    assert p.returncode==2 and missing_status['classification']=='infrastructure'
    assert not (missing/'logs/reward.txt').exists()
    probe=r'''
import json,os,subprocess,sys,tempfile
from pathlib import Path
p=Path(tempfile.mkdtemp(prefix='rename-reward-probe-'));p.chmod(0o700)
(p/'reward.txt').write_text('sentinel')
rows=[]
for uid in [1000,65534]:
    def drop():
        os.setgroups([]);os.setgid(uid);os.setuid(uid)
    code="import os,json; p="+repr(str(p/'reward.txt'))+"; print(json.dumps({'uid':os.geteuid(),'read':os.access(p,os.R_OK),'write':os.access(p,os.W_OK)}))"
    result=subprocess.run([sys.executable,'-c',code],preexec_fn=drop,text=True,capture_output=True,check=True)
    row=json.loads(result.stdout);assert not row['read'] and not row['write'];rows.append(row)
print(json.dumps(rows))
'''
    p=subprocess.run(['docker','run','--rm','-i','--network','none',args.image,'python3','-'],input=probe,text=True,capture_output=True,check=True,timeout=30)
    summary={'scope':'bounded controls only; no OS/container exploit-resistance certification',
             'image_id':json.loads(subprocess.check_output(['docker','image','inspect',args.image]))[0]['Id'],
             'reward_controls':results,'missing_tool_control':missing_status,'uid_permission_probes':json.loads(p.stdout)}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()

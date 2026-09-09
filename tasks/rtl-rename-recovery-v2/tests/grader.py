"""Trusted controller: synthesize candidate RTL, observe ports, compare history ledger.
Candidate processes never receive reference expectations and cannot write reward.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback
from protocol import Simulator,testbench,ports
from schedules import Campaign
from reference import CandidateMismatch

SOURCES=('design.sv','map_bypass.sv','ownership.sv')


def unprivileged():
    os.setgroups([])
    os.setgid(65534)
    os.setuid(65534)


def run_logged(command,path,cwd=None,drop=None,timeout=180):
    result=subprocess.run(command,cwd=cwd,preexec_fn=drop,capture_output=True,text=True,timeout=timeout)
    path.write_text(result.stdout+result.stderr)
    return result


def main():
    logs=Path(os.environ.get('VERIFIER_LOG_DIR','/logs/verifier'))
    if logs.is_symlink():
        raise RuntimeError('verifier log path must not be a symlink')
    logs.mkdir(parents=True,exist_ok=True)
    if os.geteuid()==0: os.chown(logs,0,0)
    logs.chmod(0o700)
    reward=logs/'reward.txt'; reward.unlink(missing_ok=True)
    def status(kind,**details):
        (logs/'status.json').write_text(json.dumps({'classification':kind,**details},indent=2)+'\n')
    status('infrastructure',reason='verifier not completed')
    if os.geteuid()!=0:
        status('infrastructure',reason='root verifier needed to isolate unprivileged tool processes; use supplied Docker environment')
        return 2
    for name in ('yosys','iverilog','vvp'):
        if not shutil.which(name):
            status('infrastructure',reason='missing '+name); return 2
    private=Path(tempfile.mkdtemp(prefix='rename-private-'))
    current={}; last_tool={}; campaign=None; sim=None; stages=[]
    try:
        versions={}
        for tool,args in [('yosys',['-V']),('iverilog',['-V']),('vvp',['-V'])]:
            p=run_logged([tool,*args],logs/(tool+'-version.log'),timeout=30)
            if p.returncode: raise RuntimeError(tool+' version probe failed')
            versions[tool]=(p.stdout+p.stderr).splitlines()[0]
        if not versions['yosys'].startswith('Yosys 0.23 '):
            raise RuntimeError('expected pinned Yosys 0.23')
        (logs/'versions.json').write_text(json.dumps(versions,indent=2)+'\n')
        # Tool health is checked without candidate RTL before classifying failures.
        (private/'smoke.sv').write_text('module smoke(input clk,d,output reg q); always @(posedge clk) q<=d; endmodule\n')
        p=run_logged(['yosys','-Q','-T','-p',f'read_verilog {private}/smoke.sv; hierarchy -check -top smoke; proc; opt; check -assert; write_verilog {private}/smoke-net.sv'],logs/'preflight-yosys.log',timeout=30)
        if p.returncode: raise RuntimeError('synthesis preflight failed')
        (private/'smoke-tb.sv').write_text('module tb; reg clk=0,d=1; wire q; smoke dut(.*); initial begin #1;clk=1;#1;if(q!==1) $fatal; $display("HEALTHY");$finish;end endmodule\n')
        p=run_logged(['iverilog','-g2012','-s','tb','-o',str(private/'smoke'),str(private/'smoke-net.sv'),str(private/'smoke-tb.sv')],logs/'preflight-iverilog.log',timeout=30)
        if p.returncode: raise RuntimeError('compiler preflight failed')
        p=run_logged(['vvp',str(private/'smoke')],logs/'preflight-vvp.log',timeout=30)
        if p.returncode or 'HEALTHY' not in p.stdout.splitlines(): raise RuntimeError('runtime preflight failed')
        workspace=Path(os.environ.get('TASK_WORKSPACE','/app'))
        source={}
        for name in SOURCES:
            path=workspace/name
            if not path.is_file() or path.is_symlink():
                reward.write_text('0\n'); status('candidate_source_failure',file=name); return 0
            source[name]=path.read_bytes()
        (logs/'source-sha256.json').write_text(json.dumps({n:hashlib.sha256(s).hexdigest() for n,s in source.items()},indent=2))
        (logs/'isolation.json').write_text(json.dumps({'controller_uid':os.geteuid(),'candidate_agent_user':'node','tool_and_runtime_uid':65534,'reward_directory_mode':oct(logs.stat().st_mode & 0o777),'reward_directory_uid':logs.stat().st_uid,'simulation_source':'yosys_netlist_only','reference_expectations_in_simulator':False},indent=2)+'\n')
        coverage=[]
        for phys in (16,24,32):
            for rob in (8,16):
                current={'phys':phys,'rob':rob}; pw=(phys-1).bit_length()
                prefix=logs/f'p{phys}-r{rob}'
                stage=Path(tempfile.mkdtemp(prefix='rename-tools-')); stages.append(stage)
                stage.chmod(0o700); os.chown(stage,65534,65534)
                for name,data in source.items():
                    (stage/name).write_bytes(data); (stage/name).chmod(0o444)
                script='read_verilog -sv '+' '.join(SOURCES)+f'; chparam -set PHYS {phys} -set ROB {rob} rename_recovery; hierarchy -check -top rename_recovery; proc; opt; memory; opt; check -assert; select -assert-none A:blackbox; select -assert-none t:$dlatch; write_verilog -noattr netlist.sv; write_json netlist.json'
                try:
                    p=run_logged(['yosys','-Q','-T','-p',script],prefix.with_suffix('.synthesis.log'),cwd=stage,drop=unprivileged)
                except subprocess.TimeoutExpired:
                    reward.write_text('0\n');status('candidate_synthesis_timeout',**current,limit_sec=180);return 0
                last_tool={'stage':'candidate_synthesis','returncode':p.returncode,'log':prefix.with_suffix('.synthesis.log').name}
                if p.returncode<0: raise RuntimeError('synthesis process terminated by signal '+str(-p.returncode))
                if p.returncode:
                    reward.write_text('0\n');status('candidate_synthesis_failure',**current);return 0
                description=json.loads((stage/'netlist.json').read_text())
                if any(str(module.get('attributes',{}).get('blackbox','0')).strip('0') for module in description.get('modules',{}).values()):
                    reward.write_text('0\n');status('candidate_synthesis_failure',**current,reason='black-box module is not a complete implementation');return 0
                actual=description.get('modules',{}).get('rename_recovery',{}).get('ports',{})
                expected={'clk':('input',1)}
                for direction,fields in zip(('input','output'),ports(pw)):
                    expected.update({name:(direction,width) for name,width in fields})
                observed={name:(port['direction'],len(port['bits'])) for name,port in actual.items()}
                if observed!=expected:
                    reward.write_text('0\n');status('candidate_interface_failure',**current,expected=expected,actual=observed);return 0
                # Only Yosys-emitted hardware is simulated. Original HDL system tasks,
                # candidate testbenches and success messages cannot execute in grading.
                netlist=private/f'p{phys}-r{rob}-netlist.sv'
                shutil.copyfile(stage/'netlist.sv',netlist)
                tb=private/f'p{phys}-r{rob}-tb.sv'; tb.write_text(testbench(pw))
                p=run_logged(['iverilog','-g2012','-s','tb','-o',str(stage/'sim'),str(netlist),str(tb)],prefix.with_suffix('.compile.log'),timeout=60)
                last_tool={'stage':'netlist_compile','returncode':p.returncode,'log':prefix.with_suffix('.compile.log').name}
                if p.returncode: raise RuntimeError('generated netlist/trusted testbench compilation failed; requires tool/grader review '+str(current))
                # Runtime cannot change its simulator artifact or any verifier files.
                os.chown(stage,0,0);stage.chmod(0o755)
                for path in stage.iterdir():
                    os.chown(path,0,0);path.chmod(0o444)
                sim=Simulator(['vvp',str(stage/'sim')],pw,stage,drop=unprivileged)
                campaign=Campaign(sim,phys,rob)
                try:
                    data=campaign.run()
                except (CandidateMismatch,ValueError,TimeoutError,BrokenPipeError) as exc:
                    prefix.with_suffix('.events.json').write_text(json.dumps(campaign.events,indent=2))
                    prefix.with_suffix('.observations.json').write_text(json.dumps(sim.lines,indent=2))
                    if isinstance(exc,(ValueError,BrokenPipeError)):
                        raise RuntimeError('simulator transport/protocol failure requiring tool review: '+repr(exc)) from exc
                    classification='candidate_runtime_timeout' if isinstance(exc,TimeoutError) else 'functional_failure'
                    reward.write_text('0\n');status(classification,**current,reason=str(exc),last_label=campaign.events[-1]['label'] if campaign.events else None);return 0
                finally:
                    sim.close()
                    prefix.with_suffix('.runtime.log').write_text(sim.stderr_text)
                    prefix.with_suffix('.runtime-status.json').write_text(json.dumps({'exit_code_before_controller_cleanup':sim.exit_before_close,'controller_killed_waiting_process':sim.exit_before_close is None,'final_returncode':sim.proc.returncode},indent=2)+'\n')
                    sim=None
                coverage.append({**current,**data})
                prefix.with_suffix('.coverage.json').write_text(json.dumps(data,indent=2)+'\n')
                campaign=None
        (logs/'coverage.json').write_text(json.dumps(coverage,indent=2)+'\n')
        status('functional_and_synthesis_pass',configurations=6,tool='Yosys 0.23',difficulty='uncalibrated')
        reward.write_text('1\n');return 0
    except Exception as exc:
        reward.unlink(missing_ok=True)
        (logs/'infrastructure-traceback.log').write_text(traceback.format_exc())
        status('infrastructure',reason=repr(exc),tool_process=last_tool,**current);return 2
    finally:
        if sim: sim.close()
        shutil.rmtree(private,ignore_errors=True)
        for stage in stages: shutil.rmtree(stage,ignore_errors=True)

if __name__=='__main__': sys.exit(main())

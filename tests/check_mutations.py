"""Run oracle, starter and semantic negative controls through actual graders.
Usage: python tests/check_mutations.py (Icarus and GNU timeout required).
Does not edit task assets or calibration metadata.
"""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
mutants={
'rtl-skid-flush':{
 'no-full-replacement':('count < 2 || out_ready','count < 2'),
 'ignore-flush':('rst || flush','rst'),
 'reverse-full-replacement':('q0<=q1; q1<=in_data;','q0<=in_data; q1<=q1;'),
 'accept-during-flush':('!rst && !flush && (count','!rst && (count'),
},
'rtl-rr-lock':{
 'drop-owner-with-request':("grant[owner]=1'b1","grant[owner]=req[owner]"),
 'off-by-one-fairness':('(choice+1)%N','choice%N'),
 'early-release':('if(held) begin grant','if(held && lock[owner]) begin grant'),
 'ignore-lock-acquisition':('if(lock[choice])','if(1\'b0)'),
}}
mutants['rtl-skid-flush']['truncate-to-16-bits'] = ('<=in_data', "<=(in_data & 16'hffff)")
mutants['rtl-rr-lock']['truncate-request-index'] = ('req[idx]', 'req[idx % 4]')

def main():
    for name, changes in mutants.items():
        task = ROOT / 'tasks' / name
        oracle = (task / 'solution/design.sv').read_text()
        cases = {'oracle': oracle, 'starter': (task / 'environment/repo/design.sv').read_text()}
        for label, (before, after) in changes.items():
            if before not in oracle:
                raise RuntimeError(f'Mutation no longer applies: {name}/{label}')
            cases[label] = oracle.replace(before, after)
        for label, rtl in cases.items():
            with tempfile.TemporaryDirectory(prefix='chip-mutation-') as tmp:
                workspace = Path(tmp)
                (workspace / 'design.sv').write_text(rtl)
                logs = workspace / 'logs'
                env = os.environ | {'TASK_WORKSPACE': tmp, 'VERIFIER_LOG_DIR': str(logs)}
                subprocess.run(['bash', str(task / 'tests/test.sh')], env=env, check=True, timeout=90)
                reward = int((logs / 'reward.txt').read_text())
                expected = int(label == 'oracle')
                if reward != expected:
                    raise AssertionError(f'{name}/{label}: reward {reward}, expected {expected}')
                print(f'{name}/{label}: reward {reward} as expected')

if __name__ == '__main__':
    main()

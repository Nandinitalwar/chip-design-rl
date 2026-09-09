"""Original legal event schedules driven by the independent ledger."""
import itertools
import random
from reference import Ledger


class Campaign:
    def __init__(self,sim,phys,rob):
        self.sim=sim; self.model=Ledger(phys,rob); self.events=[]
    def step(self,label,specs=(),completions=(),resolution=None,retire=0,downstream=1,rst=0,completion_ports=None):
        proposals=self.model.proposals(specs)
        args=dict(proposals=proposals,completions=completions,resolution=resolution,retire=retire,downstream=downstream,rst=rst,completion_ports=completion_ports)
        values=self.model.inputs(**args)
        self.events.append({'label':label,'inputs':values})
        obs=self.sim.exchange(values)
        return self.model.check(obs,label=label,**args)
    def reset(self):
        self.step('reset',rst=1,retire=3)
    def finish(self,label='drain'):
        pending=[r for r in self.model.transport.values() if r.pending]
        for i in range(0,len(pending),2): self.step(label+'-complete',completions=pending[i:i+2])
        for r in list(self.model.live):
            if r.branch and not r.resolved: self.step(label+'-resolve',resolution=(r,False))
        for _ in range((len(self.model.live)+1)//2+1): self.step(label+'-retire',retire=3)
        assert not self.model.live and not self.model.transport
    def directed(self):
        self.reset()
        for placement in ((0,), (1,), (0,1), (1,0)):
            self.reset()
            pair=self.step('completion-placement-setup',specs=[{'arch':1},{'arch':2}])
            self.step('completion-placement',completions=pair[:len(placement)],completion_ports=placement)
            self.step('completion-placement-ready',specs=[{'we':False,'a':1,'b':2}])
            self.finish('completion-placement-drain')
        self.reset()
        pair=self.step('same-destination-bypass',specs=[{'arch':2,'a':2},{'arch':2,'a':2,'b':0}])
        self.step('completion-no-rename-bypass',completions=pair,specs=[{'we':False,'arch':7,'a':2}])
        self.step('lane-compaction-11-01',retire=1)
        self.step('held-record-compacts',retire=0)
        self.finish()
        for branch_lane, completion_first in itertools.product((0,1),(False,True)):
            self.reset()
            specs=[{'branch':True,'we':False,'arch':6},{'arch':3,'a':3}]
            if branch_lane: specs.reverse()
            pair=self.step('checkpoint-boundary',specs=specs)
            branch=pair[branch_lane]; writer=pair[1-branch_lane]
            if completion_first: self.step('branch-complete-before-resolve',completions=[branch])
            self.step('recover-surviving-completion',resolution=(branch,True),completions=[writer],retire=0)
            self.step('post-recovery-map',specs=[{'we':False,'arch':7,'a':3},{'arch':0,'we':True,'a':0}])
            self.finish()
        self.reset()
        older=self.step('two-older-writers',specs=[{'arch':1},{'arch':2}])
        self.step('older-done',completions=older)
        b,y=self.step('branch-and-younger',specs=[{'branch':True,'we':False},{'arch':1,'a':1}])
        self.step('two-commits-plus-recovery',resolution=(b,True),retire=3,completions=[y])
        self.step('preserve-committed-recovery',specs=[{'we':False,'a':1,'b':2},{'arch':3}])
        self.finish()
        # Repeated older commits after checkpoint creation expose snapshot leaks
        # without prescribing which freed tag the legal allocator chooses next.
        self.reset()
        for round_index in range(2*self.model.phys):
            writer=self.step('commit-recovery-older',specs=[{'arch':1+round_index%7}])[0]
            branch=self.step('commit-recovery-checkpoint',specs=[{'branch':True,'we':False}])[0]
            self.step('commit-recovery-complete',completions=[writer])
            self.step('commit-after-checkpoint',retire=1)
            younger=self.step('post-commit-younger-allocation',specs=[{'arch':1+(round_index+1)%7}])[0]
            self.step('commit-freed-tag-recovery',resolution=(branch,True),completions=[branch,younger])
            self.step('commit-recovery-retire',retire=3)
        # Saturate and selectively release nested checkpoints without draining ROB.
        self.reset(); branches=[]
        for _ in range(4): branches += self.step('checkpoint-fill',specs=[{'branch':True,'we':False}])
        self.step('checkpoint-full-prefix',specs=[{'we':False},{'branch':True,'we':False}])
        self.step('checkpoint-preedge-release',resolution=(branches[2],False),specs=[{'branch':True,'we':False}])
        self.step('checkpoint-reuse',specs=[{'branch':True,'we':False}])
        self.step('nested-recovery',resolution=(branches[1],True))
        self.finish()
        # Fill both ownership and ROB resources, then test no same-edge free bypass.
        self.reset()
        for i in range(self.model.rob):
            self.step('capacity-maximal-prefix',specs=[{'arch':1+i%7},{'arch':1+(i+1)%7}])
        pending=list(self.model.live)
        for i in range(0,len(pending),2): self.step('capacity-completions',completions=pending[i:i+2])
        self.step('capacity-preedge-retire',specs=[{'arch':5},{'arch':6}],retire=3)
        self.step('capacity-next-cycle-reuse',specs=[{'arch':5},{'arch':6}],retire=3)
        self.finish()
        # Any allocator eventually reuses a killed tag: more rounds than the free set.
        self.reset(); collisions=0
        for _ in range(2*self.model.phys):
            branch,writer=self.step('late-result-new-owner',specs=[{'branch':True,'we':False},{'arch':4}])
            old=next((r for r in self.model.transport.values() if r.removed and r.pending and r.tag==writer.tag),None)
            if old:
                collisions+=1
                self.step('late-killed-physical-reuse',completions=[old],specs=[{'we':False,'a':4}])
                self.step('late-result-must-stay-unready',specs=[{'we':False,'a':4}])
            self.step('late-result-recovery',resolution=(branch,True),completions=[branch])
            self.step('late-result-branch-retire',retire=3)
        assert collisions>0
        self.finish('late-transport-drain')
        # Identity order deliberately crosses 255->0 while older work is live.
        self.reset(); self.model.next_id=254
        a,b=self.step('token-wrap-older',specs=[{'we':False},{'branch':True,'we':False}])
        self.step('token-wrap-younger',specs=[{'arch':2},{'arch':3}])
        self.step('token-wrap-recovery',resolution=(b,True),completions=[a,b])
        self.finish()
        self.reset()
        pair=self.step('reset-active-setup',specs=[{'arch':1},{'branch':True,'we':False}])
        self.step('reset-dominates-all',rst=1,completions=pair,resolution=(pair[1],True),specs=[{'arch':2}],retire=3)
        self.step('downstream-backpressure',downstream=0,specs=[{'arch':1},{'arch':2}])
        self.finish()
    def reduced_exhaustive(self):
        # Exhaustive product of these finite scenario choices, not all DUT states.
        for branch_lane,first_complete,recover,ready_prefix,dest in itertools.product(
                (0,1),(0,1),(False,True),(0,1,3),(1,2)):
            self.reset()
            specs=[{'branch':True,'we':False,'arch':5},{'arch':dest,'a':dest}]
            if branch_lane: specs.reverse()
            pair=self.step('reduced-prefix',specs=specs)
            self.step('reduced-first-completion',completions=[pair[first_complete]])
            self.step('reduced-collision',completions=[pair[1-first_complete]],
                      resolution=(pair[branch_lane],recover),retire=ready_prefix)
            self.step('reduced-successor',specs=[{'we':False,'a':dest},{'arch':dest,'a':dest}],retire=ready_prefix)
            self.finish('reduced-drain')
    def stress(self,cycles=1400):
        self.reset()
        rng=random.Random(0xA11C0000+self.model.phys*32+self.model.rob)
        for _ in range(cycles):
            pending=[r for r in self.model.transport.values() if r.pending]
            rng.shuffle(pending); completions=pending[:rng.randrange(3)]
            branches=[r for r in self.model.live if r.branch and not r.resolved]
            resolution=(rng.choice(branches),rng.randrange(4)==0) if branches and rng.randrange(3)==0 else None
            specs=[]
            for lane in range(rng.randrange(3)):
                branch=not any(p['branch'] for p in specs) and rng.randrange(6)==0
                specs.append({'branch':branch,'we':not branch and rng.randrange(5)!=0,
                              'arch':rng.randrange(8),'a':rng.randrange(8),'b':rng.randrange(8)})
            self.step('seeded-stress',specs=specs,completions=completions,resolution=resolution,
                      retire=rng.choice((0,1,3)),downstream=int(rng.randrange(9)!=0),
                      completion_ports=rng.sample((0,1),len(completions)))
        self.finish('stress-drain')
    def run(self):
        self.directed(); self.reduced_exhaustive(); self.stress()
        return {'cycles':self.model.cycles,'accepted':self.model.accepted,'retired':self.model.retired,
                'killed':self.model.killed,'labels':self.model.labels,
                'seed':0xA11C0000+self.model.phys*32+self.model.rob}

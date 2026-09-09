"""Independent transaction/history ledger. Accepts any legal allocator choices."""
from dataclasses import dataclass


class CandidateMismatch(Exception):
    pass


@dataclass
class Instruction:
    ident: int
    arch: int
    effective: bool
    branch: bool
    tag: int
    stale: int
    done: bool=False
    resolved: bool=False
    removed: bool=False
    pending: bool=True


class Ledger:
    def __init__(self,phys,rob):
        self.phys=phys; self.rob=rob; self.pw=(phys-1).bit_length()
        self.live=[]; self.transport={}; self.committed=list(range(8)); self.next_id=0
        self.cycles=0; self.accepted=0; self.retired=0; self.killed=0; self.reset_discarded=0; self.labels={}
    def owned(self):
        return set(self.committed)|{r.tag for r in self.live if r.effective}
    def maps(self):
        mapping=self.committed.copy(); ready={p:True for p in self.committed}
        for r in self.live:
            if r.effective:
                mapping[r.arch]=r.tag; ready[r.tag]=r.done
        return mapping,ready
    def proposals(self,specs):
        answer=[]; chosen=set()
        for spec in specs:
            for _ in range(256):
                ident=self.next_id; self.next_id=(ident+1)%256
                if ident not in self.transport and ident not in chosen: break
            else: break
            chosen.add(ident)
            lane={'id':ident,'arch':spec.get('arch',1),'we':spec.get('we',True),
                  'branch':spec.get('branch',False),'a':spec.get('a',0),'b':spec.get('b',0)}
            assert not lane['branch'] or not lane['we']
            answer.append(lane)
        return answer
    def inputs(self,proposals=(),completions=(),resolution=None,retire=0,downstream=1,rst=0,completion_ports=None):
        assert len(proposals)<=2 and len(completions)<=2
        assert sum(x['branch'] for x in proposals)<=1
        assert len({x.ident for x in completions})==len(completions)
        assert all(x.pending and self.transport[x.ident] is x for x in completions)
        assert all(x['id'] not in self.transport for x in proposals)
        assert len({x['id'] for x in proposals})==len(proposals)
        assert retire in (0,1,3)
        if resolution:
            assert resolution[0] in self.live and resolution[0].branch and not resolution[0].resolved
        completion_ports=list(range(len(completions))) if completion_ports is None else completion_ports
        assert len(completion_ports)==len(completions) and len(set(completion_ports))==len(completion_ports)
        assert all(port in (0,1) for port in completion_ports)
        values={'rst':rst,'downstream_ready':downstream,'dispatch_valid':(1<<len(proposals))-1,
                'retire_ready':retire,'complete_valid':sum(1<<port for port in completion_ports)}
        for i,p in enumerate(proposals):
            for port,key,w in [('dispatch_id','id',8),('dispatch_src_a','a',3),('dispatch_src_b','b',3),
                               ('dispatch_dst','arch',3),('dispatch_dst_we','we',1),('dispatch_branch','branch',1)]:
                values[port]=values.get(port,0)|(int(p[key])<<(i*w))
        for i,r in zip(completion_ports,completions):
            values['complete_id']=values.get('complete_id',0)|(r.ident<<(8*i))
            values['complete_dst']=values.get('complete_dst',0)|(r.tag<<(self.pw*i))
        if resolution:
            values.update(resolve_valid=1,resolve_id=resolution[0].ident,resolve_recover=int(resolution[1]))
        return values
    def check(self,obs,proposals=(),completions=(),resolution=None,retire=0,downstream=1,rst=0,label='mixed',completion_ports=None):
        def equal(actual,expected,field):
            if actual!=expected:
                raise CandidateMismatch({'field':field,'expected':expected,'actual':actual,'label':label,
                                         'cycle':self.cycles,'live':[vars(r).copy() for r in self.live],
                                         'committed':self.committed.copy()})
        self.cycles+=1; self.labels[label]=self.labels.get(label,0)+1
        recovery=bool(resolution and resolution[1])
        free=set(range(self.phys))-self.owned()
        room=self.rob-len(self.live); checkpoints=4-sum(r.branch and not r.resolved for r in self.live)
        num_accept=0
        if not rst and downstream and not recovery:
            for p in proposals:
                effective=p['we'] and p['arch']!=0
                if room==0 or (effective and len(free)<sum(x['we'] and x['arch']!=0 for x in proposals[:num_accept])+1) or (p['branch'] and checkpoints==0): break
                room-=1; checkpoints-=int(p['branch']); num_accept+=1
        equal(obs.get('dispatch_accept'),(1<<num_accept)-1,'dispatch_accept')
        offered=[]
        if not rst:
            for r in self.live[:2]:
                if not r.done or (r.branch and not r.resolved) or (recovery and self.live.index(r)>=self.live.index(resolution[0])): break
                offered.append(r)
        equal(obs.get('retire_valid'),(1<<len(offered))-1,'retire_valid')
        for i,r in enumerate(offered):
            for port,value,w in [('retire_id',r.ident,8),('retire_arch_dst',r.arch,3),('retire_dst_we',int(r.effective),1),
                                 ('retire_branch',int(r.branch),1),('retire_dst',r.tag,self.pw),('retire_stale',r.stale,self.pw)]:
                equal(obs.get(port,i,w),value,port+str(i))
        mapping,ready=self.maps(); new=[]
        for i,p in enumerate(proposals[:num_accept]):
            for suffix,key in [('a','a'),('b','b')]:
                tag=mapping[p[key]]
                equal(obs.get('renamed_src_'+suffix,i,self.pw),tag,'source-'+suffix+str(i))
                equal(obs.get('renamed_src_'+suffix+'_ready',i,1),int(ready[tag]),'ready-'+suffix+str(i))
            effective=p['we'] and p['arch']!=0
            tag=obs.get('renamed_dst',i,self.pw); stale=obs.get('renamed_stale',i,self.pw)
            if effective:
                if tag not in free: raise CandidateMismatch({'field':'allocation','tag':tag,'free':sorted(free),'label':label})
                free.remove(tag)
                equal(stale,mapping[p['arch']],'stale'+str(i))
                mapping[p['arch']]=tag; ready[tag]=False
            else:
                equal(tag,0,'no-dest-tag'); equal(stale,0,'no-dest-stale')
            new.append(Instruction(p['id'],p['arch'],effective,p['branch'],tag,stale,resolved=not p['branch']))
        if rst:
            self.reset_discarded+=len(self.live)
            self.live=[]; self.transport={}; self.committed=list(range(8))
            return []
        transferred=[r for i,r in enumerate(offered) if retire & (1<<i)]
        for r in transferred:
            assert self.live.pop(0) is r
            if r.effective:
                equal(r.stale,self.committed[r.arch],'committed-stale-consistency')
                self.committed[r.arch]=r.tag
            r.removed=True; self.retired+=1
        if resolution:
            branch,recover=resolution
            if recover:
                boundary=self.live.index(branch)+1
                for r in self.live[boundary:]: r.removed=True; self.killed+=1
                self.live=self.live[:boundary]
            branch.resolved=True
        for r in completions:
            r.pending=False
            if not r.removed: r.done=True
        for r in new:
            self.live.append(r); self.transport[r.ident]=r
        self.accepted+=len(new)
        self.transport={key:r for key,r in self.transport.items() if r.pending or not r.removed}
        tags=[r.tag for r in self.live if r.effective]
        assert len(set(tags))==len(tags) and not set(tags)&set(self.committed)
        assert self.accepted==self.retired+self.killed+self.reset_discarded+len(self.live)
        return new

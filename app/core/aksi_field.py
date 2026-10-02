"""AKSI Dynamic Cognitive Field v1."""
from __future__ import annotations
import hashlib, math, re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Optional
TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9]+")
def tokens(text: str) -> List[str]: return [x.lower() for x in TOKEN_RE.findall(text or "") if len(x)>1][:96]
def hvec(token: str, dim: int=64) -> Tuple[float,...]:
    h=hashlib.sha256(token.encode("utf-8")).digest(); return tuple(1.0 if ((h[i%len(h)]>>(i%8))&1) else -1.0 for i in range(dim))
def normalize(v):
    z=math.sqrt(sum(x*x for x in v)) or 1.0; return [x/z for x in v]
def encode(text: str, dim: int=64):
    out=[0.0]*dim; ts=tokens(text)
    for i,tok in enumerate(ts):
        for j,x in enumerate(hvec(tok,dim)): out[j]+=x
        if i:
            for j,x in enumerate(hvec(ts[i-1]+"|"+tok,dim)): out[j]+=0.6*x
    return normalize(out)
def cosine(a,b): return sum(x*y for x,y in zip(a,b))
def entropy(counts):
    n=sum(counts.values())
    return 0.0 if not n else -sum((c/n)*math.log2(c/n) for c in counts.values() if c)
@dataclass
class FieldState:
    step:int=0; energy:float=0.0; entropy:float=0.0; confidence:float=0.0; stability:float=1.0; prediction_error:float=0.0
    spectrum:List[float]=field(default_factory=lambda:[0.0]*16); active_operators:List[str]=field(default_factory=list)
    attractors:Dict[str,int]=field(default_factory=dict); transitions:Dict[str,int]=field(default_factory=dict); memory_size:int=0; history:List[Dict[str,Any]]=field(default_factory=list)
class DynamicField:
    GENOME=("hdc","markov","spectral","attractor","uncertainty","stability","counterfactual")
    def __init__(self,dim=64): self.dim=dim; self.state=FieldState(); self.memory={}; self.last_vector=None; self.last_tokens=[]
    def _spectrum(self,ts):
        bins=[0.0]*16
        for i,tok in enumerate(ts):
            d=hashlib.sha256(tok.encode()).digest(); k=d[0]%16; phase=d[1]/255*math.tau; bins[k]+=1+0.25*math.sin(phase+i*0.618)
        z=math.sqrt(sum(x*x for x in bins)) or 1.0; return [x/z for x in bins]
    def _markov(self,ts):
        for a,b in zip(ts,ts[1:]): self.state.transitions[f"{a}→{b}"]=self.state.transitions.get(f"{a}→{b}",0)+1
    def _attractor(self,v):
        k=hashlib.sha256(",".join(f"{x:.3f}" for x in v).encode()).hexdigest()[:12]; self.state.attractors[k]=self.state.attractors.get(k,0)+1; return k
    def _select(self,ts,evidence,uncertainty):
        ops=["hdc"]
        if len(ts)>=2: ops.append("markov")
        if len(ts)>=3: ops.append("spectral")
        if evidence: ops.append("uncertainty")
        if uncertainty>0.35: ops.append("counterfactual")
        if len(self.state.history)>=2: ops.append("stability")
        if self.memory: ops.append("attractor")
        return [x for x in self.GENOME if x in ops]
    def step(self,observation,*,external_evidence=0,confidence=None):
        ts=tokens(observation); v=encode(observation,self.dim); u=1-max(0,min(1,confidence if confidence is not None else 0.5))
        predicted=None
        if self.last_tokens and ts:
            cs=[k.split("→",1)[1] for k,n in self.state.transitions.items() if k.startswith(self.last_tokens[-1]+"→") and n>0]
            predicted=max(cs,key=lambda x:self.state.transitions[self.last_tokens[-1]+"→"+x],default=None)
        actual=ts[0] if ts else None; error=0.0 if predicted is None or predicted==actual else 1.0
        ops=self._select(ts,external_evidence,u)
        if "markov" in ops: self._markov(ts)
        attractor=self._attractor(v) if ("attractor" in ops and self.memory) else None
        energy=min(1.0,0.55*(1-cosine(v,self.last_vector))+0.45*u) if self.last_vector else u
        stability=max(0.0,min(1.0,1-0.5*abs(energy-self.state.energy)-0.35*error))
        hist=(self.state.history+[{"step":self.state.step+1,"observation":observation[:240],"energy":round(energy,6),"prediction_error":error,"stability":round(stability,6),"operators":ops}])[-64:]
        self.state=FieldState(self.state.step+1,round(energy,6),round(entropy(Counter(ts)),6),round(1-u,6),round(stability,6),round(error,6),self._spectrum(ts) if "spectral" in ops else [0.0]*16,ops,dict(self.state.attractors),dict(self.state.transitions),len(self.memory),hist)
        key=attractor or hashlib.sha256(observation.encode()).hexdigest()[:12]; self.memory[key]={"observation":observation[:1000],"vector":v,"step":self.state.step}; self.last_vector,self.last_tokens=v,ts
        return self.snapshot()
    def counterfactual(self,actions):
        b=self.state; out=[]
        for action in actions[:8]:
            v=encode(action,self.dim); novelty=1-max(0,cosine(v,self.last_vector or v)); risk=min(1,0.45*novelty+0.55*(1-b.stability)); utility=0.55*novelty+0.45*b.confidence
            out.append({"action":action,"utility":round(utility,4),"risk":round(risk,4),"score":round(utility-risk,4),"stability":round(b.stability,4)})
        return sorted(out,key=lambda x:x["score"],reverse=True)
    def snapshot(self):
        s=self.state; return {"step":s.step,"state_vector":"X=(V,M,E,F,H,P,C,Sigma)","energy":s.energy,"entropy":s.entropy,"confidence":s.confidence,"stability":s.stability,"prediction_error":s.prediction_error,"spectrum":s.spectrum,"active_operators":s.active_operators,"attractor_count":len(s.attractors),"transition_count":len(s.transitions),"memory_size":len(self.memory),"history":s.history[-12:]}
_SESSIONS: Dict[str, DynamicField] = {}
_MAX_SESSIONS = 128

def get_field(session_id: Optional[str] = None) -> tuple[Optional[str], DynamicField]:
    if not session_id:
        return None, DynamicField()
    if session_id not in _SESSIONS:
        if len(_SESSIONS) >= _MAX_SESSIONS:
            _SESSIONS.pop(next(iter(_SESSIONS)))
        _SESSIONS[session_id] = DynamicField()
    return session_id, _SESSIONS[session_id]

def run_field(observation,evidence=None,confidence=None,session_id=None):
    sid, f = get_field(session_id)
    result=f.step(observation,external_evidence=len(evidence or []),confidence=confidence)
    return {"session_id":sid,"field":result,"counterfactuals":f.counterfactual(["continue current trajectory","seek more evidence","switch strategy"])}
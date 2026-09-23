"""AKSI Semantic Sampling — minimal sufficient evidence for agent execution.

Research implementation, not a theorem. It samples semantic state transitions rather
than every journal message, and exposes explicit unknown gaps instead of inventing
unobserved behavior.
"""
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

CRITICAL_KINDS = {"intent","plan","source","decision","action","verification","permission","result","error","completion"}

def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()

def classify(message: str, status: str = "") -> str:
    m=(message or "").lower(); s=(status or "").lower()
    if any(x in m for x in ("разреш","permission","approval","доступ")): return "permission"
    if any(x in m for x in ("план","plan")): return "plan"
    if any(x in m for x in ("источ","source","search","найдено","прочитано")): return "source"
    if any(x in m for x in ("browser","click","type","navigate")): return "action"
    if any(x in m for x in ("провер","verify","вериф","доказ")): return "verification"
    if any(x in m for x in ("ошиб","failed","failure","warning","не удалось")) or s=="error": return "error"
    if any(x in m for x in ("готов","completed","заверш")) or s=="completed": return "completion"
    if any(x in m for x in ("цель","goal","задач")): return "intent"
    if any(x in m for x in ("анализ","analysis","реш","вывод")): return "decision"
    if any(x in m for x in ("результ","report","отчёт")): return "result"
    return "observation"

def semantic_state(task: Dict[str, Any]) -> Dict[str, Any]:
    sources=task.get("sources") or []; browser=task.get("browser") or {}; verification=task.get("verification") or {}
    domains=set()
    for x in sources:
        if isinstance(x,dict):
            u=str(x.get("url",""))
            if u.startswith(("http://","https://")): domains.add(u.split("/")[2].lower())
    return {"status":task.get("status"),"plan_len":len(task.get("plan") or []),"journal_len":len(task.get("journal") or []),
            "sources":len(sources),"source_domains":len(domains),"browser_steps":len(browser.get("steps") or []) if isinstance(browser,dict) else 0,
            "analysis_ready":bool(task.get("analysis")),"verification_status":verification.get("status"),
            "findings":len(task.get("findings") or []),"report_ready":bool(task.get("report")),"receipt_ready":bool(task.get("receipt"))}

def semantic_delta(previous: Optional[Dict[str,Any]], current: Dict[str,Any]) -> float:
    if previous is None: return 1.0
    keys=sorted(set(previous)|set(current))
    return sum(previous.get(k)!=current.get(k) for k in keys)/len(keys) if keys else 0.0

@dataclass
class SampleDecision:
    sampled: bool
    reason: str
    delta: float

class SemanticSampler:
    def __init__(self, threshold: float=0.18, max_gap: int=8):
        self.threshold=max(0.0,min(1.0,threshold)); self.max_gap=max(1,int(max_gap))
    def init(self)->Dict[str,Any]:
        return {"version":"AKSI-SS/0.1","threshold":self.threshold,"max_gap":self.max_gap,"events_total":0,"checkpoints":[],"last_state":None,"last_checkpoint_seq":-1}
    def observe(self, runtime: Dict[str,Any], message: str, status: str)->Dict[str,Any]:
        sampling=runtime.setdefault("sampling",self.init()); seq=int(sampling["events_total"]); sampling["events_total"]=seq+1
        kind=classify(message,status); state=semantic_state(runtime); delta=semantic_delta(sampling.get("last_state"),state)
        gap=seq-int(sampling.get("last_checkpoint_seq",-1))
        if seq==0: reason="first"; sampled=True
        elif kind in CRITICAL_KINDS: reason=f"critical:{kind}"; sampled=True
        elif delta>=self.threshold: reason="semantic_delta"; sampled=True
        elif gap>=self.max_gap: reason="max_gap"; sampled=True
        else: reason="discarded"; sampled=False
        if sampled:
            sampling["checkpoints"].append({"seq":seq,"kind":kind,"status":status,"message_hash":sha256(message or ""),
                "state":state,"state_hash":sha256(state),"delta":round(delta,6),"reason":reason})
            sampling["last_checkpoint_seq"]=seq; sampling["last_state"]=state
        return {"seq":seq,"kind":kind,"sampled":sampled,"reason":reason,"delta":round(delta,6)}

def reconstruct_from_checkpoints(checkpoints: Sequence[Dict[str,Any]], total_events: int):
    by_seq={int(c["seq"]):c for c in checkpoints}; out=[]; current=None
    for seq in range(max(0,int(total_events))):
        if seq in by_seq: current=by_seq[seq]["state"]; out.append({"seq":seq,"known":True,"state":current})
        else: out.append({"seq":seq,"known":False,"state":current})
    return out

def reconstruction_metrics(full_states, checkpoints):
    total=len(full_states)
    if total==0: return {"events":0,"checkpoints":0,"compression_ratio":0.0,"state_error_rate":0.0}
    recon=reconstruct_from_checkpoints(checkpoints,total); known=0; mismatches=0
    for truth,pred in zip(full_states,recon):
        if pred["known"]:
            known+=1
            if pred["state"]!=truth: mismatches+=1
    return {"events":total,"checkpoints":len(checkpoints),"compression_ratio":round(len(checkpoints)/total,6),
            "known_event_rate":round(known/total,6),"checkpoint_state_error_rate":round(mismatches/max(1,known),6),
            "unobserved_event_rate":round(1-known/total,6)}

def finalize(runtime: Dict[str,Any])->Dict[str,Any]:
    sampling=runtime.get("sampling") or {}; events=int(sampling.get("events_total",0)); cps=sampling.get("checkpoints") or []
    return {"protocol":sampling.get("version","AKSI-SS/0.1"),"events":events,"checkpoints":len(cps),
            "compression_ratio":round(len(cps)/events,6) if events else 0.0,
            "checkpoint_rate_percent":round((len(cps)/events)*100,2) if events else 0.0,
            "max_gap":sampling.get("max_gap"),"threshold":sampling.get("threshold"),
            "last_checkpoint_seq":sampling.get("last_checkpoint_seq",-1),"trace_hash":sha256(cps),
            "claim":"cryptographic evidence of sampled runtime state; unobserved intervals remain unproven"}
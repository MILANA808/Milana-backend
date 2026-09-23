"""Executable synthetic benchmark for AKSI semantic sampling.
Run: python research/aksi_sampling_benchmark.py
"""
from __future__ import annotations
import math, random, statistics

def make_trace(T,dims,transitions,rng):
    cuts=sorted(rng.sample(range(20,T-20),transitions)); state=[rng.uniform(-1,1) for _ in range(dims)]; trace=[]; cutset=set(cuts)
    for i in range(T):
        if i in cutset: state=[max(-1,min(1,x+rng.uniform(-0.9,0.9))) for x in state]
        jitter=[rng.gauss(0,0.025) for _ in range(dims)]; trace.append([state[d]+jitter[d] for d in range(dims)])
    return trace

def uniform_indices(T,budget):
    return sorted(set(round(i*(T-1)/(budget-1)) for i in range(budget)))

def adaptive_indices(trace,threshold=0.30,max_gap=35):
    out=[0]; last=trace[0]; last_idx=0
    for i in range(1,len(trace)):
        delta=math.sqrt(sum((trace[i][d]-last[d])**2 for d in range(len(trace[i]))))
        if delta>=threshold or i-last_idx>=max_gap: out.append(i); last=trace[i]; last_idx=i
    if out[-1]!=len(trace)-1: out.append(len(trace)-1)
    return out

def reconstruct(trace,indices):
    out=[trace[indices[0]]]*len(trace)
    for a,b in zip(indices,indices[1:]):
        for i in range(a,b+1): out[i]=trace[a]
    for i in range(indices[-1],len(trace)): out[i]=trace[indices[-1]]
    return out

def rmse(a,b):
    n=sum(len(x) for x in a); return math.sqrt(sum((x[d]-y[d])**2 for x,y in zip(a,b) for d in range(len(x)))/n)

def run(seed=42,runs=500):
    ue,ae,ac=[],[],[]
    for r in range(runs):
        rng=random.Random(seed+r); trace=make_trace(1000,4,rng.randint(8,24),rng)
        u=uniform_indices(1000,40); a=adaptive_indices(trace)
        ue.append(rmse(trace,reconstruct(trace,u))); ae.append(rmse(trace,reconstruct(trace,a))); ac.append(len(a))
    ratios=[a/u for a,u in zip(ae,ue) if u>0]
    return {"runs":runs,"uniform_mean_checkpoints":40,"adaptive_mean_checkpoints":statistics.mean(ac),
            "uniform_mean_rmse":statistics.mean(ue),"adaptive_mean_rmse":statistics.mean(ae),
            "median_error_ratio_adaptive_over_uniform":statistics.median(ratios),
            "adaptive_win_rate":sum(a<u for a,u in zip(ae,ue))/runs}

if __name__=="__main__": print(run())
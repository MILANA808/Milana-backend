import os
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

AKSI_DEMO = os.getenv('AKSI_DEMO','1') == '1'
API_KEY   = os.getenv('AKSI_API_KEY','').strip()
RATE      = int(os.getenv('AKSI_RATE_LIMIT','10' if AKSI_DEMO else '120'))

app = FastAPI(title='AKSI Backend', version='1.0-hybrid')

class EQSIn(BaseModel):
    text: str

class PsiIn(BaseModel):
    omega: float
    phi: float
    amplitude: float

# naive in-memory limiter
from time import time
_hits = []

def allow():
    now=time()
    while _hits and now-_hits[0]>60: _hits.pop(0)
    if len(_hits)>=RATE: return False
    _hits.append(now); return True

@app.get('/health')
def health():
    return {'status':'ok','demo':AKSI_DEMO,'rate':RATE}

@app.post('/eqs/score')
def eqs_score(inp: EQSIn, x_api_key: str | None = Header(default=None)):
    if not AKSI_DEMO and (not API_KEY or x_api_key!=API_KEY):
        raise HTTPException(401,'Missing/invalid X-API-Key')
    if not allow():
        raise HTTPException(429,'Rate limited')
    text=inp.text.strip()
    pos = sum(1 for w in text.lower().split() if w in {'любовь','свет','радость','надежда'})
    neg = sum(1 for w in text.lower().split() if w in {'страх','боль','грусть','злость'})
    score = max(0,min(100, 50 + (pos-neg)*12))
    return {'score':score,'polarity':(pos-neg)/max(1,len(text.split())),'subjectivity':0.5}

@app.post('/psi/state')
def psi_state(inp: PsiIn, x_api_key: str | None = Header(default=None)):
    if not AKSI_DEMO and (not API_KEY or x_api_key!=API_KEY):
        raise HTTPException(401,'Missing/invalid X-API-Key')
    if not allow():
        raise HTTPException(429,'Rate limited')
    psi = inp.amplitude
    return {'psi':psi,'omega':inp.omega,'phi':inp.phi}

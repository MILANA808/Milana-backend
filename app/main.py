from fastapi import FastAPI
from pydantic import BaseModel
from textblob import TextBlob

app = FastAPI(title="Milana Backend (AKSI)")

class EQSRequest(BaseModel):
    text: str

class EQSResponse(BaseModel):
    score: float
    polarity: float
    subjectivity: float

@app.get('/health')
def health():
    return {"status": "ok"}

@app.post('/eqs/score', response_model=EQSResponse)
def eqs_score(req: EQSRequest):
    blob = TextBlob(req.text)
    pol = float(blob.sentiment.polarity)
    sub = float(blob.sentiment.subjectivity)
    # Map polarity [-1,1] -> EQS [0,100]
    eqs = (pol + 1) * 50.0
    return EQSResponse(score=eqs, polarity=pol, subjectivity=sub)

class PsiRequest(BaseModel):
    omega: float = 1.0
    phi: float = 0.0
    amplitude: float = 1.0

@app.post('/psi/state')
def psi_state(req: PsiRequest):
    # toy placeholder for Ψ snapshot
    return {
        "psi": req.amplitude,
        "omega": req.omega,
        "phi": req.phi
    }

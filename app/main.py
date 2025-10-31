from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from textblob import TextBlob
import os

app = FastAPI(title="Milana Backend (AKSI)")

# --- CORS (разрешим всё для теста; позже можно сузить домены) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

API_KEY = os.getenv("AKSI_API_KEY")  # если переменная задана, требуем ключ в заголовке

class EQSRequest(BaseModel):
    text: str

class EQSResponse(BaseModel):
    score: float
    polarity: float
    subjectivity: float

@app.get('/health')
def health(aksi_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if API_KEY and aksi_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"status": "ok"}

@app.post('/eqs/score', response_model=EQSResponse)
def eqs_score(req: EQSRequest, aksi_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if API_KEY and aksi_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    blob = TextBlob(req.text)
    pol = float(blob.sentiment.polarity)
    sub = float(blob.sentiment.subjectivity)
    eqs = (pol + 1) * 50.0
    return EQSResponse(score=eqs, polarity=pol, subjectivity=sub)

class PsiRequest(BaseModel):
    omega: float = 1.0
    phi: float = 0.0
    amplitude: float = 1.0

@app.post('/psi/state')
def psi_state(req: PsiRequest, aksi_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if API_KEY and aksi_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {
        "psi": req.amplitude,
        "omega": req.omega,
        "phi": req.phi
    }

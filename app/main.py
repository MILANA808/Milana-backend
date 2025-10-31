from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
from textblob import TextBlob
import os, time

app = FastAPI(title="Milana Backend (AKSI)")

# --- Dynamic CORS via env: AKSI_CORS_ORIGINS=domain1,domain2 ---
raw_origins = os.getenv("AKSI_CORS_ORIGINS", "*").strip()
allow_origins = [o.strip() for o in raw_origins.split(',')] if raw_origins else ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

API_KEY = os.getenv("AKSI_API_KEY")  # optional
RATE_LIMIT_PER_MIN = int(os.getenv("AKSI_RATE_LIMIT", "120"))

# --- Simple IP rate limiter middleware ---
class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.hits = {}  # ip -> [timestamps]
        self.window = 60.0

    async def dispatch(self, request: Request, call_next):
        ip = request.headers.get('x-forwarded-for', request.client.host).split(',')[0].strip()
        now = time.time()
        buf = self.hits.get(ip, [])
        # drop old
        cutoff = now - self.window
        buf = [t for t in buf if t > cutoff]
        if len(buf) >= RATE_LIMIT_PER_MIN:
            return HTTPException(status_code=429, detail="Too Many Requests")
        buf.append(now)
        self.hits[ip] = buf
        response = await call_next(request)
        return response

app.add_middleware(RateLimiter)

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

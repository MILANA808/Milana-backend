from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from textblob import TextBlob
import os, time

app = FastAPI(title="Milana Backend (AKSI)")

raw_origins = os.getenv("AKSI_CORS_ORIGINS", "*").strip()
allow_origins = [o.strip() for o in raw_origins.split(',')] if raw_origins else ['*']
app.add_middleware(CORSMiddleware, allow_origins=allow_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

API_KEY = os.getenv("AKSI_API_KEY")
RATE_LIMIT_PER_MIN = int(os.getenv("AKSI_RATE_LIMIT", "120"))

class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.hits = {}
        self.window = 60.0
    async def dispatch(self, request: Request, call_next):
        ip = request.headers.get('x-forwarded-for', request.client.host).split(',')[0].strip()
        now = time.time()
        buf = self.hits.get(ip, [])
        cutoff = now - self.window
        buf = [t for t in buf if t > cutoff]
        if len(buf) >= RATE_LIMIT_PER_MIN:
            return JSONResponse({"detail": "Too Many Requests"}, status_code=429)
        buf.append(now)
        self.hits[ip] = buf
        return await call_next(request)

app.add_middleware(RateLimiter)

class EQSRequest(BaseModel):
    text: str
class EQSResponse(BaseModel):
    score: float; polarity: float; subjectivity: float
class PsiRequest(BaseModel):
    omega: float = 1.0; phi: float = 0.0; amplitude: float = 1.0

def _check_key(k: str | None):
    if API_KEY and k != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get('/', response_class=HTMLResponse)
def home():
    return "<h1>AKSI EQS</h1><p>Откройте <a href='/docs'>/docs</a> для теста API.</p>"

@app.get('/health')
def health(aksi_api_key: str | None = Header(default=None, alias="X-API-Key")):
    _check_key(aksi_api_key); return {"status": "ok"}

@app.post('/eqs/score', response_model=EQSResponse)
def eqs_score(req: EQSRequest, aksi_api_key: str | None = Header(default=None, alias="X-API-Key")):
    _check_key(aksi_api_key)
    blob = TextBlob(req.text)
    pol = float(blob.sentiment.polarity); sub = float(blob.sentiment.subjectivity)
    eqs = (pol + 1) * 50.0
    return EQSResponse(score=eqs, polarity=pol, subjectivity=sub)

@app.post('/psi/state')
def psi_state(req: PsiRequest, aksi_api_key: str | None = Header(default=None, alias="X-API-Key")):
    _check_key(aksi_api_key)
    return {"psi": req.amplitude, "omega": req.omega, "phi": req.phi}

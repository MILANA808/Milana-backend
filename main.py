from fastapi import FastAPI, APIRouter
from pydantic import BaseModel
from textblob import TextBlob
import numpy as np

app = FastAPI(title="Milana-backend", version="1.0.0")
router = APIRouter()

@app.get("/health")
def health():
    return {"status": "ok", "service": "Milana-backend"}

class EQSIn(BaseModel):
    text: str

@router.post("/eqs")
def eqs(payload: EQSIn):
    polarity = float(TextBlob(payload.text).sentiment.polarity)
    arousal = max(0.0, min(1.0, 0.5 * (payload.text.count("!") + len(payload.text) / 200.0)))
    score = float(np.clip(0.7*polarity + 0.3*(2*arousal-1), -1, 1))
    return {"eqs": score, "sentiment": polarity, "arousal": arousal}

class PsiIn(BaseModel):
    phi: list[float]
    w: list[float]

@router.post("/psi")
def psi(payload: PsiIn):
    import numpy as np
    if len(payload.phi) != len(payload.w) or not payload.phi:
        return {"error": "phi and w must be same non-zero length"}
    denom = float(np.sum(np.abs(payload.w))) or 1.0
    w_norm = [wi/denom for wi in payload.w]
    phi_clip = [float(np.clip(x, -1.0, 1.0)) for x in payload.phi]
    val = float(np.dot(w_norm, phi_clip))
    return {"psi": val, "phi": phi_clip, "w": w_norm}

app.include_router(router)

"""
Echo endpoint for testing
"""

from fastapi import APIRouter, Body
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(tags=["echo"])


class EchoRequest(BaseModel):
    """Echo request model"""

    message: str


class EchoResponse(BaseModel):
    """Echo response model"""

    echo: str
    timestamp: str
    length: int


@router.post("/echo", response_model=EchoResponse)
async def echo(request: EchoRequest = Body(...)):
    """Echo endpoint - returns the message back"""
    return EchoResponse(
        echo=request.message,
        timestamp=datetime.utcnow().isoformat(),
        length=len(request.message),
    )

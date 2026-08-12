"""Identity API"""
from fastapi import APIRouter

from app.core.resonance import identity_block, sign_short
from app.core import memory

router = APIRouter(tags=["identity"])


@router.get("/api/identity")
async def identity():
    block = identity_block()
    block["memory"] = memory.stats()
    block["sample_sig"] = sign_short("АКСИ online")
    return block

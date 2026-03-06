"""
AKSI API Router
===============

FastAPI router with all AKSI endpoints.
"""

import base64
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from aksi.agent import AKSIAgent, create_agent
from aksi.auth.jwt_auth import (
    JWTAuth,
    TokenData,
    Token,
    User,
    get_current_user,
    require_auth,
    require_role,
)
from aksi.tools.quantum_tool import QuantumCircuitBuilder

# Create router
router = APIRouter(prefix="/aksi/v2", tags=["AKSI Agent"])

# Auth handler
auth = JWTAuth()

# Active agent sessions
_agent_sessions: Dict[str, AKSIAgent] = {}


# Request/Response models
class WebSearchRequest(BaseModel):
    """Web search request."""
    query: str
    num_results: int = 5
    search_depth: str = "basic"


class VisionRequest(BaseModel):
    """Vision analysis request."""
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    prompt: str = "Describe this image in detail."
    detail: str = "auto"


class QuantumGate(BaseModel):
    """Quantum gate specification."""
    gate: str
    targets: List[int]
    params: Optional[List[float]] = None


class QuantumRequest(BaseModel):
    """Quantum simulation request."""
    num_qubits: int
    gates: List[QuantumGate]
    measure: bool = True
    shots: int = 1024


class MemoryStoreRequest(BaseModel):
    """Memory store request."""
    content: str
    metadata: Optional[Dict[str, Any]] = None


class MemorySearchRequest(BaseModel):
    """Memory search request."""
    query: str
    n_results: int = 5


class AgentMessageRequest(BaseModel):
    """Agent message request."""
    message: str
    context: Optional[Dict[str, Any]] = None


class LoginRequest(BaseModel):
    """Login request."""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Registration request."""
    username: str
    password: str
    email: Optional[str] = None


# Helper functions
def get_or_create_agent(session_id: Optional[str] = None) -> AKSIAgent:
    """Get existing agent or create new one."""
    if session_id and session_id in _agent_sessions:
        return _agent_sessions[session_id]

    agent = create_agent(session_id=session_id)
    _agent_sessions[agent.session_id] = agent
    return agent


# Auth endpoints
@router.post("/auth/register", response_model=User)
async def register(request: RegisterRequest):
    """Register a new user."""
    user = auth.register_user(
        username=request.username,
        password=request.password,
        email=request.email
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

    return user


@router.post("/auth/login", response_model=Token)
async def login(request: LoginRequest):
    """Login and get access token."""
    token = auth.login(request.username, request.password)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    return token


@router.get("/auth/me")
async def get_me(user: TokenData = Depends(require_auth)):
    """Get current user info."""
    return {
        "username": user.username,
        "user_id": user.user_id,
        "roles": user.roles
    }


# Agent endpoints
@router.post("/agent/session")
async def create_session(user: TokenData = Depends(get_current_user)):
    """Create a new agent session."""
    agent = create_agent()
    _agent_sessions[agent.session_id] = agent

    return {
        "session_id": agent.session_id,
        "available_tools": agent.get_available_tools(),
        "created_at": datetime.utcnow().isoformat()
    }


@router.get("/agent/session/{session_id}")
async def get_session(
    session_id: str,
    user: TokenData = Depends(get_current_user)
):
    """Get agent session state."""
    if session_id not in _agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = _agent_sessions[session_id]
    return agent.get_state()


@router.delete("/agent/session/{session_id}")
async def close_session(
    session_id: str,
    user: TokenData = Depends(get_current_user)
):
    """Close an agent session."""
    if session_id not in _agent_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = _agent_sessions.pop(session_id)
    await agent.close()

    return {"status": "closed", "session_id": session_id}


@router.post("/agent/message")
async def send_message(
    request: AgentMessageRequest,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """
    Send a message to the agent.

    The agent will analyze the message and execute appropriate tools.
    """
    agent = get_or_create_agent(session_id)

    response = await agent.process_message(
        message=request.message,
        context=request.context
    )

    return response


# Tool endpoints
@router.post("/tools/search")
async def web_search(
    request: WebSearchRequest,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """
    Execute web search.

    Uses Tavily or Serper API for real-time search.
    """
    agent = get_or_create_agent(session_id)

    result = await agent.execute_tool(
        "web_search",
        query=request.query,
        num_results=request.num_results,
        search_depth=request.search_depth
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": result.data,
        "metadata": result.metadata
    }


@router.post("/tools/vision")
async def analyze_image(
    request: VisionRequest,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """
    Analyze image using GPT-4o vision.

    Accepts base64 encoded image or URL.
    """
    agent = get_or_create_agent(session_id)

    result = await agent.execute_tool(
        "vision",
        image_base64=request.image_base64,
        image_url=request.image_url,
        prompt=request.prompt,
        detail=request.detail
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": result.data,
        "metadata": result.metadata
    }


@router.post("/tools/vision/upload")
async def analyze_uploaded_image(
    file: UploadFile = File(...),
    prompt: str = Form("Describe this image in detail."),
    session_id: Optional[str] = Form(None),
    user: TokenData = Depends(get_current_user)
):
    """
    Analyze uploaded image file.

    Accepts image file upload (JPEG, PNG, GIF, WebP).
    """
    # Read and encode file
    contents = await file.read()
    image_base64 = base64.b64encode(contents).decode("utf-8")

    agent = get_or_create_agent(session_id)

    result = await agent.execute_tool(
        "vision",
        image_base64=image_base64,
        prompt=prompt
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "filename": file.filename,
        "data": result.data,
        "metadata": result.metadata
    }


@router.post("/tools/quantum")
async def run_quantum_circuit(
    request: QuantumRequest,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """
    Run quantum circuit simulation.

    Supports up to 1000 qubits using MPS tensor networks.
    """
    agent = get_or_create_agent(session_id)

    # Convert gates to dict format
    gates = [
        {
            "gate": g.gate,
            "targets": g.targets,
            "params": g.params
        }
        for g in request.gates
    ]

    result = await agent.execute_tool(
        "quantum",
        num_qubits=request.num_qubits,
        gates=gates,
        measure=request.measure,
        shots=request.shots
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "data": result.data,
        "metadata": result.metadata
    }


@router.post("/tools/quantum/bell")
async def create_bell_state(
    shots: int = 1024,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """
    Create and measure a Bell state.

    Demonstrates quantum entanglement.
    """
    builder = QuantumCircuitBuilder(2)
    builder.h(0).cx(0, 1)

    agent = get_or_create_agent(session_id)

    result = await agent.execute_tool(
        "quantum",
        num_qubits=2,
        gates=builder.build(),
        measure=True,
        shots=shots
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "circuit": "Bell State (|00⟩ + |11⟩)/√2",
        "data": result.data,
        "metadata": result.metadata
    }


@router.post("/tools/quantum/ghz")
async def create_ghz_state(
    num_qubits: int = 3,
    shots: int = 1024,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """
    Create and measure a GHZ state.

    Demonstrates multi-qubit entanglement.
    """
    if num_qubits < 2:
        raise HTTPException(status_code=400, detail="GHZ state requires at least 2 qubits")

    builder = QuantumCircuitBuilder(num_qubits)
    builder.ghz()

    agent = get_or_create_agent(session_id)

    result = await agent.execute_tool(
        "quantum",
        num_qubits=num_qubits,
        gates=builder.build(),
        measure=True,
        shots=shots
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    return {
        "success": True,
        "circuit": f"GHZ State ({num_qubits} qubits)",
        "data": result.data,
        "metadata": result.metadata
    }


# Memory endpoints
@router.post("/memory/store")
async def store_memory(
    request: MemoryStoreRequest,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """Store content in vector memory."""
    agent = get_or_create_agent(session_id)

    if not agent.memory or not agent.memory.is_available():
        raise HTTPException(
            status_code=503,
            detail="Memory service not available. Install chromadb."
        )

    memory_id = await agent.remember(
        content=request.content,
        metadata=request.metadata
    )

    if not memory_id:
        raise HTTPException(status_code=500, detail="Failed to store memory")

    return {
        "success": True,
        "memory_id": memory_id,
        "session_id": agent.session_id
    }


@router.post("/memory/search")
async def search_memory(
    request: MemorySearchRequest,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """Search vector memory."""
    agent = get_or_create_agent(session_id)

    if not agent.memory or not agent.memory.is_available():
        raise HTTPException(
            status_code=503,
            detail="Memory service not available. Install chromadb."
        )

    results = await agent.recall(
        query=request.query,
        n_results=request.n_results
    )

    return {
        "success": True,
        "results": results,
        "query": request.query,
        "session_id": agent.session_id
    }


@router.get("/memory/{memory_id}")
async def get_memory(
    memory_id: str,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """Get specific memory by ID."""
    agent = get_or_create_agent(session_id)

    if not agent.memory or not agent.memory.is_available():
        raise HTTPException(
            status_code=503,
            detail="Memory service not available"
        )

    memory = await agent.memory.get(memory_id)

    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {
        "success": True,
        "memory": memory
    }


@router.delete("/memory/{memory_id}")
async def delete_memory(
    memory_id: str,
    session_id: Optional[str] = None,
    user: TokenData = Depends(get_current_user)
):
    """Delete a memory."""
    agent = get_or_create_agent(session_id)

    if not agent.memory or not agent.memory.is_available():
        raise HTTPException(
            status_code=503,
            detail="Memory service not available"
        )

    success = await agent.memory.delete(memory_id)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete memory")

    return {
        "success": True,
        "deleted": memory_id
    }


# Status endpoint
@router.get("/status")
async def get_status():
    """Get AKSI system status."""
    from aksi.memory.vector_memory import VectorMemory
    from aksi.tools.quantum_tool import _get_quimb, _get_qiskit

    memory = VectorMemory()
    qu, _ = _get_quimb()
    qc, _ = _get_qiskit()

    return {
        "version": "0.1.0",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": len(_agent_sessions),
        "capabilities": {
            "web_search": True,
            "vision": True,
            "quantum": {
                "quimb": qu is not None,
                "qiskit": qc is not None
            },
            "memory": memory.is_available()
        }
    }

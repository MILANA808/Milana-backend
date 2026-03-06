#!/usr/bin/env python3
"""
AKSI Modules Test Script
========================

Tests for AKSI agent modules without requiring external API keys.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_config():
    """Test configuration module."""
    print("Testing config module...")

    from aksi.config import settings, AKSISettings

    assert settings is not None
    assert settings.jwt_algorithm == "HS256"
    assert settings.quantum_max_qubits == 1000

    # Test custom settings
    custom = AKSISettings(jwt_secret_key="test-key")
    assert custom.jwt_secret_key == "test-key"

    print("  [OK] Config module works")


def test_tool_base():
    """Test base tool class."""
    print("Testing tool base class...")

    from aksi.tools.base import BaseTool, ToolResult

    # Test ToolResult
    result = ToolResult(success=True, data={"test": 123})
    assert result.success is True
    assert result.data["test"] == 123

    result_error = ToolResult(success=False, error="Test error")
    assert result_error.success is False
    assert result_error.error == "Test error"

    print("  [OK] Tool base class works")


def test_web_search_tool():
    """Test web search tool (without API key)."""
    print("Testing web search tool...")

    from aksi.tools.web_search import WebSearchTool

    tool = WebSearchTool()

    assert tool.name == "web_search"
    assert tool.description is not None

    schema = tool.get_schema()
    assert "parameters" in schema
    assert "query" in schema["parameters"]["properties"]

    print("  [OK] Web search tool initializes correctly")


def test_vision_tool():
    """Test vision tool (without API key)."""
    print("Testing vision tool...")

    from aksi.tools.vision import VisionTool

    tool = VisionTool()

    assert tool.name == "vision"
    assert tool.description is not None

    # Test image type detection
    assert tool._detect_image_type("/9j/") == "jpeg"
    assert tool._detect_image_type("iVBORw0KGgo") == "png"
    assert tool._detect_image_type("R0lGOD") == "gif"
    assert tool._detect_image_type("UklGR") == "webp"
    assert tool._detect_image_type("unknown") == "jpeg"  # Default

    print("  [OK] Vision tool initializes correctly")


def test_quantum_tool():
    """Test quantum tool."""
    print("Testing quantum tool...")

    from aksi.tools.quantum_tool import QuantumTool, QuantumCircuitBuilder

    tool = QuantumTool()

    assert tool.name == "quantum"
    assert tool.max_qubits == 1000
    assert "h" in tool.SUPPORTED_GATES
    assert "cx" in tool.SUPPORTED_GATES

    # Test circuit builder
    builder = QuantumCircuitBuilder(3)
    builder.h(0).cx(0, 1).cx(1, 2)
    gates = builder.build()

    assert len(gates) == 3
    assert gates[0]["gate"] == "h"
    assert gates[1]["gate"] == "cx"

    # Test GHZ builder
    ghz_builder = QuantumCircuitBuilder(4)
    ghz_builder.ghz()
    ghz_gates = ghz_builder.build()

    assert ghz_gates[0]["gate"] == "h"
    assert ghz_gates[0]["targets"] == [0]
    # Should have 1 H + 3 CNOT gates
    assert len(ghz_gates) == 4

    print("  [OK] Quantum tool works")


def test_jwt_auth():
    """Test JWT authentication."""
    print("Testing JWT auth...")

    from aksi.auth.jwt_auth import JWTAuth, TokenData

    auth = JWTAuth(secret_key="test-secret-key")

    # Test user registration
    user = auth.register_user(
        username="testuser",
        password="testpass123",
        email="test@example.com",
        roles=["user", "developer"]
    )

    assert user is not None
    assert user.username == "testuser"
    assert "user" in user.roles

    # Test duplicate registration fails
    duplicate = auth.register_user("testuser", "otherpass")
    assert duplicate is None

    # Test authentication
    auth_user = auth.authenticate_user("testuser", "testpass123")
    assert auth_user is not None
    assert auth_user.username == "testuser"

    # Test wrong password
    wrong = auth.authenticate_user("testuser", "wrongpass")
    assert wrong is None

    # Test token creation and verification
    try:
        token = auth.create_access_token(
            data={"sub": "testuser", "user_id": user.user_id, "roles": user.roles}
        )

        assert token is not None
        assert len(token) > 0

        # Verify token
        token_data = auth.verify_token(token)
        assert token_data is not None
        assert token_data.username == "testuser"
        assert "user" in token_data.roles

        print("  [OK] JWT auth works (with python-jose)")
    except RuntimeError:
        print("  [SKIP] python-jose not installed")

    # Test login flow
    try:
        login_token = auth.login("testuser", "testpass123")
        assert login_token is not None
        assert login_token.token_type == "bearer"
        print("  [OK] Login flow works")
    except RuntimeError:
        print("  [SKIP] Login requires python-jose")


def test_memory():
    """Test vector memory (without ChromaDB)."""
    print("Testing memory module...")

    from aksi.memory.vector_memory import VectorMemory

    memory = VectorMemory()

    # Check if ChromaDB is available
    if memory.is_available():
        print("  [OK] ChromaDB is available")
    else:
        print("  [INFO] ChromaDB not installed - memory will be disabled")

    print("  [OK] Memory module loads correctly")


async def test_agent():
    """Test AKSI agent."""
    print("Testing AKSI agent...")

    from aksi.agent import AKSIAgent, create_agent

    # Create agent
    agent = create_agent(session_id="test-session")

    assert agent.session_id == "test-session"
    assert "web_search" in agent.tools
    assert "vision" in agent.tools
    assert "quantum" in agent.tools

    # Test state
    state = agent.get_state()
    assert state["session_id"] == "test-session"
    assert state["is_active"] is True

    # Test available tools
    tools = agent.get_available_tools()
    assert len(tools) == 3

    # Close agent
    await agent.close()
    assert agent.state.is_active is False

    print("  [OK] AKSI agent works")


async def test_quantum_execution():
    """Test quantum circuit execution if quimb/qiskit available."""
    print("Testing quantum execution...")

    from aksi.agent import create_agent

    agent = create_agent()

    # Try to run a simple Bell state
    result = await agent.run_quantum_circuit(
        num_qubits=2,
        gates=[
            {"gate": "h", "targets": [0]},
            {"gate": "cx", "targets": [0, 1]}
        ],
        measure=True,
        shots=100
    )

    if result.success:
        print(f"  [OK] Quantum simulation works: {result.data}")
        assert "counts" in result.data
        # Bell state should produce |00> and |11> approximately equally
        counts = result.data["counts"]
        print(f"  [OK] Bell state counts: {counts}")
    else:
        print(f"  [SKIP] Quantum simulation not available: {result.error}")

    await agent.close()


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("AKSI Modules Test Suite")
    print("=" * 60)
    print()

    # Synchronous tests
    test_config()
    test_tool_base()
    test_web_search_tool()
    test_vision_tool()
    test_quantum_tool()
    test_jwt_auth()
    test_memory()

    # Async tests
    asyncio.run(test_agent())
    asyncio.run(test_quantum_execution())

    print()
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()

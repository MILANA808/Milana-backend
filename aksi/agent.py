"""
AKSI Agent Module
=================

Main agent class that orchestrates tools and workflow.
Implements an agentic workflow pattern.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel

from aksi.tools.base import BaseTool, ToolResult
from aksi.tools.web_search import WebSearchTool
from aksi.tools.vision import VisionTool
from aksi.tools.quantum_tool import QuantumTool
from aksi.memory.vector_memory import VectorMemory
from aksi.config import settings

logger = logging.getLogger(__name__)


class AgentMessage(BaseModel):
    """Message in agent conversation."""

    role: str  # user, assistant, system, tool
    content: str
    timestamp: datetime = None
    tool_name: Optional[str] = None
    tool_result: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow()
        super().__init__(**data)


class AgentState(BaseModel):
    """Current state of the agent."""

    session_id: str
    messages: List[AgentMessage] = []
    tool_calls: List[Dict[str, Any]] = []
    memory_context: List[Dict[str, Any]] = []
    is_active: bool = True
    started_at: datetime = None
    last_activity: datetime = None

    def __init__(self, **data):
        if "started_at" not in data:
            data["started_at"] = datetime.utcnow()
        if "last_activity" not in data:
            data["last_activity"] = datetime.utcnow()
        super().__init__(**data)


class AKSIAgent:
    """
    AKSI Superintelligence Agent.

    Orchestrates tools for:
    - Web search (Tavily/Serper)
    - Vision analysis (GPT-4o)
    - Quantum simulation (quimb/Qiskit)
    - Vector memory (ChromaDB)
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        enable_memory: bool = True,
        custom_tools: Optional[List[BaseTool]] = None
    ):
        """
        Initialize AKSI agent.

        Args:
            session_id: Unique session identifier
            enable_memory: Whether to enable vector memory
            custom_tools: Additional custom tools to register
        """
        import secrets
        self.session_id = session_id or secrets.token_hex(8)
        self.state = AgentState(session_id=self.session_id)

        # Initialize tools
        self.tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

        if custom_tools:
            for tool in custom_tools:
                self.register_tool(tool)

        # Initialize memory
        self.memory: Optional[VectorMemory] = None
        if enable_memory:
            self.memory = VectorMemory()

        # Tool execution hooks
        self._pre_tool_hooks: List[Callable] = []
        self._post_tool_hooks: List[Callable] = []

        logger.info(f"AKSI Agent initialized: session={self.session_id}")

    def _register_default_tools(self):
        """Register default AKSI tools."""
        self.register_tool(WebSearchTool())
        self.register_tool(VisionTool())
        self.register_tool(QuantumTool())

    def register_tool(self, tool: BaseTool):
        """
        Register a tool with the agent.

        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool
        logger.debug(f"Tool registered: {tool.name}")

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get schemas for all available tools.

        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self.tools.values()]

    async def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """
        Execute a specific tool.

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            ToolResult from tool execution
        """
        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                error=f"Tool not found: {tool_name}"
            )

        tool = self.tools[tool_name]

        # Execute pre-hooks
        for hook in self._pre_tool_hooks:
            await hook(tool_name, kwargs)

        # Execute tool
        try:
            result = await tool.execute(**kwargs)
        except Exception as e:
            result = ToolResult(
                success=False,
                error=f"Tool execution error: {str(e)}"
            )

        # Record tool call
        self.state.tool_calls.append({
            "tool": tool_name,
            "params": kwargs,
            "success": result.success,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Execute post-hooks
        for hook in self._post_tool_hooks:
            await hook(tool_name, kwargs, result)

        # Update state
        self.state.last_activity = datetime.utcnow()

        return result

    async def search_web(
        self,
        query: str,
        num_results: int = 5
    ) -> ToolResult:
        """
        Convenience method for web search.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            Search results
        """
        return await self.execute_tool(
            "web_search",
            query=query,
            num_results=num_results
        )

    async def analyze_image(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        prompt: str = "Describe this image."
    ) -> ToolResult:
        """
        Convenience method for image analysis.

        Args:
            image_base64: Base64 encoded image
            image_url: URL of image
            prompt: Analysis prompt

        Returns:
            Image analysis result
        """
        return await self.execute_tool(
            "vision",
            image_base64=image_base64,
            image_url=image_url,
            prompt=prompt
        )

    async def run_quantum_circuit(
        self,
        num_qubits: int,
        gates: List[Dict[str, Any]],
        measure: bool = True,
        shots: int = 1024
    ) -> ToolResult:
        """
        Convenience method for quantum simulation.

        Args:
            num_qubits: Number of qubits
            gates: List of gate operations
            measure: Whether to measure
            shots: Number of shots

        Returns:
            Quantum simulation result
        """
        return await self.execute_tool(
            "quantum",
            num_qubits=num_qubits,
            gates=gates,
            measure=measure,
            shots=shots
        )

    async def remember(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Store content in long-term memory.

        Args:
            content: Content to remember
            metadata: Additional metadata

        Returns:
            Memory ID if successful
        """
        if not self.memory:
            return None

        return await self.memory.store(
            content=content,
            metadata={
                "session_id": self.session_id,
                **(metadata or {})
            }
        )

    async def recall(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search long-term memory.

        Args:
            query: Search query
            n_results: Number of results

        Returns:
            List of relevant memories
        """
        if not self.memory:
            return []

        return await self.memory.search(query, n_results)

    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and determine actions.

        This is the main entry point for agentic workflow.

        Args:
            message: User message
            context: Additional context

        Returns:
            Response with actions taken
        """
        # Add message to state
        self.state.messages.append(AgentMessage(
            role="user",
            content=message
        ))

        # Search memory for relevant context
        memory_context = []
        if self.memory and self.memory.is_available():
            memory_context = await self.recall(message, n_results=3)
            self.state.memory_context = memory_context

        # Analyze intent and determine tools to use
        # (In production, this would use an LLM for intent detection)
        response = {
            "session_id": self.session_id,
            "message": message,
            "memory_context": memory_context,
            "available_tools": [t.name for t in self.tools.values()],
            "tool_calls": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        # Simple keyword-based tool detection (placeholder for LLM)
        message_lower = message.lower()

        if any(word in message_lower for word in ["search", "find", "look up", "google"]):
            result = await self.search_web(message)
            response["tool_calls"].append({
                "tool": "web_search",
                "result": result.data if result.success else result.error
            })

        if any(word in message_lower for word in ["quantum", "qubit", "circuit"]):
            # Example: run a simple Bell state
            result = await self.run_quantum_circuit(
                num_qubits=2,
                gates=[
                    {"gate": "h", "targets": [0]},
                    {"gate": "cx", "targets": [0, 1]}
                ]
            )
            response["tool_calls"].append({
                "tool": "quantum",
                "result": result.data if result.success else result.error
            })

        # Record response
        self.state.messages.append(AgentMessage(
            role="assistant",
            content=str(response)
        ))

        self.state.last_activity = datetime.utcnow()

        return response

    def add_pre_tool_hook(self, hook: Callable):
        """Add a pre-tool execution hook."""
        self._pre_tool_hooks.append(hook)

    def add_post_tool_hook(self, hook: Callable):
        """Add a post-tool execution hook."""
        self._post_tool_hooks.append(hook)

    def get_state(self) -> Dict[str, Any]:
        """
        Get current agent state.

        Returns:
            Agent state as dictionary
        """
        return {
            "session_id": self.session_id,
            "is_active": self.state.is_active,
            "message_count": len(self.state.messages),
            "tool_calls_count": len(self.state.tool_calls),
            "started_at": self.state.started_at.isoformat(),
            "last_activity": self.state.last_activity.isoformat(),
            "available_tools": list(self.tools.keys())
        }

    async def close(self):
        """Clean up agent resources."""
        self.state.is_active = False
        logger.info(f"AKSI Agent closed: session={self.session_id}")


# Factory function for creating agents
def create_agent(
    session_id: Optional[str] = None,
    enable_memory: bool = True
) -> AKSIAgent:
    """
    Create a new AKSI agent instance.

    Args:
        session_id: Optional session identifier
        enable_memory: Whether to enable vector memory

    Returns:
        New AKSIAgent instance
    """
    return AKSIAgent(session_id=session_id, enable_memory=enable_memory)

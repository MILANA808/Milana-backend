#!/usr/bin/env python3
"""
AKSI Agent Workflow Example
============================

This example demonstrates the agentic workflow pattern with AKSI,
showing how to use tools for web search, vision, and quantum simulation.

Note: Some features require API keys to be configured:
- Web search: AKSI_TAVILY_API_KEY or AKSI_SERPER_API_KEY
- Vision: AKSI_OPENAI_API_KEY
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aksi.agent import AKSIAgent, create_agent
from aksi.tools.base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Example custom tool: Simple calculator."""

    name = "calculator"
    description = "Perform basic arithmetic calculations"

    async def execute(
        self,
        operation: str,
        a: float,
        b: float
    ) -> ToolResult:
        """Execute calculation."""
        try:
            if operation == "add":
                result = a + b
            elif operation == "subtract":
                result = a - b
            elif operation == "multiply":
                result = a * b
            elif operation == "divide":
                if b == 0:
                    return ToolResult(success=False, error="Division by zero")
                result = a / b
            else:
                return ToolResult(success=False, error=f"Unknown operation: {operation}")

            return ToolResult(
                success=True,
                data={
                    "operation": operation,
                    "a": a,
                    "b": b,
                    "result": result
                }
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


async def basic_agent_example():
    """Basic agent creation and tool execution."""
    print("=" * 50)
    print("Basic Agent Example")
    print("=" * 50)
    print()

    # Create agent with custom tool
    agent = AKSIAgent(
        session_id="example-session",
        enable_memory=False,  # Disable memory for this example
        custom_tools=[CalculatorTool()]
    )

    print("Available tools:")
    for tool in agent.get_available_tools():
        print(f"  - {tool['name']}: {tool['description']}")
    print()

    # Execute calculator tool
    print("Executing calculator: 42 + 58 =")
    result = await agent.execute_tool(
        "calculator",
        operation="add",
        a=42,
        b=58
    )

    if result.success:
        print(f"  Result: {result.data['result']}")
    else:
        print(f"  Error: {result.error}")

    # Get agent state
    state = agent.get_state()
    print()
    print(f"Agent state:")
    print(f"  Session ID: {state['session_id']}")
    print(f"  Tool calls: {state['tool_calls_count']}")
    print(f"  Available tools: {state['available_tools']}")

    await agent.close()
    print()


async def web_search_example():
    """Web search tool example."""
    print("=" * 50)
    print("Web Search Example")
    print("=" * 50)
    print()

    agent = create_agent()

    # Try web search
    result = await agent.search_web(
        query="quantum computing applications 2024",
        num_results=3
    )

    if result.success:
        print("Search results:")
        for item in result.data.get("results", [])[:3]:
            print(f"  - {item['title']}")
            print(f"    {item['url']}")
            print()
    else:
        print(f"Search not available: {result.error}")
        print("Note: Configure AKSI_TAVILY_API_KEY or AKSI_SERPER_API_KEY")

    await agent.close()
    print()


async def quantum_agent_example():
    """Quantum simulation through agent."""
    print("=" * 50)
    print("Quantum Agent Example")
    print("=" * 50)
    print()

    agent = create_agent()

    # Create a 3-qubit GHZ state
    print("Creating 3-qubit GHZ state...")

    result = await agent.run_quantum_circuit(
        num_qubits=3,
        gates=[
            {"gate": "h", "targets": [0]},
            {"gate": "cx", "targets": [0, 1]},
            {"gate": "cx", "targets": [0, 2]}
        ],
        measure=True,
        shots=500
    )

    if result.success:
        print(f"Backend: {result.data.get('backend', 'unknown')}")
        print("Measurement results:")
        for state, count in sorted(result.data["counts"].items(), key=lambda x: -x[1]):
            prob = count / result.data["shots"] * 100
            print(f"  |{state}⟩: {count} ({prob:.1f}%)")
    else:
        print(f"Error: {result.error}")

    await agent.close()
    print()


async def message_processing_example():
    """Agent message processing example."""
    print("=" * 50)
    print("Message Processing Example")
    print("=" * 50)
    print()

    agent = create_agent()

    # Process a message that triggers quantum tool
    print("Processing message: 'Run a quantum experiment'")
    response = await agent.process_message(
        message="Run a quantum experiment with entanglement"
    )

    print()
    print(f"Agent response:")
    print(f"  Session ID: {response['session_id']}")
    print(f"  Tool calls made: {len(response['tool_calls'])}")

    for call in response['tool_calls']:
        print(f"    - {call['tool']}: {'success' if call.get('result') else 'no result'}")

    await agent.close()
    print()


async def tool_hooks_example():
    """Example with pre/post tool execution hooks."""
    print("=" * 50)
    print("Tool Hooks Example")
    print("=" * 50)
    print()

    agent = create_agent()

    # Add hooks
    async def log_before(tool_name, params):
        print(f"  [PRE] About to execute: {tool_name}")

    async def log_after(tool_name, params, result):
        status = "SUCCESS" if result.success else "FAILED"
        print(f"  [POST] {tool_name}: {status}")

    agent.add_pre_tool_hook(log_before)
    agent.add_post_tool_hook(log_after)

    print("Executing quantum tool with hooks:")

    result = await agent.run_quantum_circuit(
        num_qubits=2,
        gates=[{"gate": "h", "targets": [0]}],
        measure=True,
        shots=10
    )

    if result.success:
        print()
        print(f"  Result: {len(result.data['counts'])} unique states measured")

    await agent.close()
    print()


async def main():
    """Run all examples."""
    print()
    print("AKSI Agent Workflow Examples")
    print("============================")
    print()

    await basic_agent_example()
    await web_search_example()
    await quantum_agent_example()
    await message_processing_example()
    await tool_hooks_example()

    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

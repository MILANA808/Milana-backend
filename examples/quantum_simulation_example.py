#!/usr/bin/env python3
"""
AKSI Quantum Simulation Example
================================

This example demonstrates quantum circuit simulation using AKSI's
tensor network-based simulator (MPS) that can handle up to 1000 qubits.

Examples:
- Bell state creation
- GHZ entanglement
- Quantum Fourier Transform (QFT)
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aksi.agent import create_agent
from aksi.tools.quantum_tool import QuantumCircuitBuilder


async def bell_state_example():
    """Create and measure a Bell state |Φ+⟩ = (|00⟩ + |11⟩)/√2"""
    print("=" * 50)
    print("Bell State Example")
    print("=" * 50)
    print()
    print("Circuit: H(q0) → CNOT(q0, q1)")
    print("Expected: |00⟩ and |11⟩ with ~50% probability each")
    print()

    agent = create_agent()

    result = await agent.run_quantum_circuit(
        num_qubits=2,
        gates=[
            {"gate": "h", "targets": [0]},
            {"gate": "cx", "targets": [0, 1]}
        ],
        measure=True,
        shots=1000
    )

    if result.success:
        print(f"Backend: {result.data.get('backend', 'unknown')}")
        print(f"Measurement results ({result.data['shots']} shots):")
        for state, count in sorted(result.data["counts"].items()):
            prob = count / result.data["shots"] * 100
            print(f"  |{state}⟩: {count} ({prob:.1f}%)")
    else:
        print(f"Error: {result.error}")

    await agent.close()
    print()


async def ghz_state_example(num_qubits=5):
    """Create a GHZ state with multiple qubits"""
    print("=" * 50)
    print(f"GHZ State Example ({num_qubits} qubits)")
    print("=" * 50)
    print()
    print(f"Circuit: H(q0) → CNOT(q0,q1) → CNOT(q0,q2) → ... → CNOT(q0,q{num_qubits-1})")
    print(f"Expected: |{'0'*num_qubits}⟩ and |{'1'*num_qubits}⟩ with ~50% each")
    print()

    agent = create_agent()

    # Use circuit builder
    builder = QuantumCircuitBuilder(num_qubits)
    builder.ghz()

    result = await agent.run_quantum_circuit(
        num_qubits=num_qubits,
        gates=builder.build(),
        measure=True,
        shots=1000
    )

    if result.success:
        print(f"Backend: {result.data.get('backend', 'unknown')}")
        print(f"Measurement results ({result.data['shots']} shots):")
        for state, count in sorted(result.data["counts"].items(), key=lambda x: -x[1]):
            prob = count / result.data["shots"] * 100
            print(f"  |{state}⟩: {count} ({prob:.1f}%)")
    else:
        print(f"Error: {result.error}")

    await agent.close()
    print()


async def superposition_example(num_qubits=10):
    """Create equal superposition state"""
    print("=" * 50)
    print(f"Superposition Example ({num_qubits} qubits)")
    print("=" * 50)
    print()
    print(f"Circuit: H on all {num_qubits} qubits")
    print(f"Expected: Uniform distribution over 2^{num_qubits} = {2**num_qubits} states")
    print()

    agent = create_agent()

    # Apply H to all qubits
    gates = [{"gate": "h", "targets": [i]} for i in range(num_qubits)]

    result = await agent.run_quantum_circuit(
        num_qubits=num_qubits,
        gates=gates,
        measure=True,
        shots=500
    )

    if result.success:
        print(f"Backend: {result.data.get('backend', 'unknown')}")
        print(f"Total unique states measured: {len(result.data['counts'])}")
        print(f"Top 5 most frequent states:")
        sorted_counts = sorted(result.data["counts"].items(), key=lambda x: -x[1])
        for state, count in sorted_counts[:5]:
            prob = count / result.data["shots"] * 100
            print(f"  |{state}⟩: {count} ({prob:.1f}%)")
    else:
        print(f"Error: {result.error}")

    await agent.close()
    print()


async def large_scale_example(num_qubits=50):
    """Demonstrate large-scale simulation with MPS"""
    print("=" * 50)
    print(f"Large-Scale MPS Simulation ({num_qubits} qubits)")
    print("=" * 50)
    print()
    print("This demonstrates AKSI's ability to simulate circuits")
    print("beyond classical statevector limits using Matrix Product States.")
    print()

    agent = create_agent()

    # Create a simple circuit that's tractable for MPS
    # (low entanglement structure)
    gates = []

    # Initial superposition
    gates.append({"gate": "h", "targets": [0]})

    # Linear entanglement chain
    for i in range(num_qubits - 1):
        gates.append({"gate": "cx", "targets": [i, i + 1]})

    result = await agent.run_quantum_circuit(
        num_qubits=num_qubits,
        gates=gates,
        measure=True,
        shots=100
    )

    if result.success:
        print(f"Backend: {result.data.get('backend', 'unknown')}")
        print(f"Successfully simulated {num_qubits}-qubit circuit!")
        print(f"Gates applied: {result.data['gates_applied']}")
        print(f"Unique measurement outcomes: {len(result.data['counts'])}")

        # Show sample results
        print(f"\nSample measurement outcomes:")
        sorted_counts = sorted(result.data["counts"].items(), key=lambda x: -x[1])
        for state, count in sorted_counts[:3]:
            # Truncate long bitstrings for display
            display_state = state if len(state) <= 20 else f"{state[:10]}...{state[-10:]}"
            print(f"  |{display_state}⟩: {count} times")
    else:
        print(f"Error: {result.error}")
        print("Note: Large-scale simulation requires quimb to be installed.")

    await agent.close()
    print()


async def main():
    """Run all examples."""
    print()
    print("AKSI Quantum Simulation Examples")
    print("=================================")
    print()
    print("These examples demonstrate AKSI's quantum simulation capabilities")
    print("using tensor networks (MPS) for efficient large-scale simulation.")
    print()

    # Run examples
    await bell_state_example()
    await ghz_state_example(5)
    await superposition_example(10)
    await large_scale_example(50)

    print("=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

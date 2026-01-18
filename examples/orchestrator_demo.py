"""
Orchestrator demonstration

Shows how the orchestrator coordinates all agents using
Reflective Autonomy v2 and Deep Causality Engine
"""

from aksi_agents.orchestrator import AKSIOrchestrator
from aksi_agents.logger import AKSILogger


def demo_orchestrator():
    """Demonstrate orchestrator workflow"""
    print("=== AKSI Orchestrator Demo ===\n")

    # Initialize
    logger = AKSILogger()
    orchestrator = AKSIOrchestrator(logger)

    # Show initial stats
    print("Initial Statistics:")
    stats = orchestrator.get_stats()
    for key, value in stats.items():
        if key != "autonomy_metrics":
            print(f"  {key}: {value}")
    print()

    # Simulate analysis workflow
    print("Running analysis workflow...")
    print("  (In production, this runs in background)")
    print()

    # Manual workflow simulation
    repository = "example-org/example-repo"

    # Step 1: Research
    print("1. AI-Researcher analyzing repository...")
    research = orchestrator.researcher.analyze_repository(repository)
    print(f"   Found {len(research.patterns)} patterns")

    # Step 2: Causality analysis
    print("2. Deep Causality Engine analyzing root causes...")
    causality = orchestrator.causality.analyze_causality(
        {"repository": repository},
        {"patterns": research.patterns, "similar_issues": research.similar_issues}
    )
    print(f"   Root cause: {causality.root_cause}")
    print(f"   Confidence: {causality.confidence:.2f}")

    # Step 3: Autonomy decision
    print("3. Reflective Autonomy evaluating decision...")
    decision = orchestrator.autonomy.evaluate_decision(
        context={"research": research, "causality": causality},
        proposed_action="create_issue",
        alternatives=["analyze", "update"]
    )
    print(f"   Decision: {decision.decision_type}")
    print(f"   Confidence: {decision.confidence:.2f}")
    print(f"   Reasoning: {', '.join(decision.reasoning)}")

    # Step 4: Action (if confidence is high)
    if decision.confidence >= 0.6:
        print("4. Executing action (confidence threshold met)...")
        result = orchestrator._create_issue_workflow(repository, research, causality)
        print(f"   Action: {result['action']}")
        if result["action"] == "issue_created":
            print(f"   Issue title: {result['variant'].title}")
            print(f"   Validation score: {result['validation'].score:.2f}")
    else:
        print("4. Action skipped (confidence too low)")

    print()

    # Final stats
    print("Final Statistics:")
    stats = orchestrator.get_stats()
    for key, value in stats.items():
        if key != "autonomy_metrics":
            print(f"  {key}: {value}")

    print("\nAutonomy Metrics:")
    autonomy_metrics = stats["autonomy_metrics"]
    for key, value in autonomy_metrics.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo_orchestrator()

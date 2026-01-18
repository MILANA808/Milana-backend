"""
AKSI Orchestrator with Reflective Autonomy v2 + Deep Causality Engine
Coordinates all agents and makes autonomous decisions
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import time

from .researcher import AIResearcher
from .writer import AIWriter
from .validator import AIValidator
from .integrator import AIIntegrator


@dataclass
class Decision:
    """Decision made by the orchestrator"""
    decision_id: str
    decision_type: str  # create_issue, update_issue, close_issue, create_pr
    confidence: float  # 0.0 - 1.0
    reasoning: List[str]
    actions: List[Any]
    timestamp: float = field(default_factory=time.time)


@dataclass
class CausalityChain:
    """Deep causality analysis chain"""
    root_cause: str
    contributing_factors: List[str]
    expected_outcomes: List[str]
    confidence: float


class ReflectiveAutonomyEngine:
    """
    Reflective Autonomy v2
    - Self-evaluates decisions
    - Learns from patterns
    - Adjusts behavior based on outcomes
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.decision_history = []
        self.performance_metrics = {
            "decisions_made": 0,
            "successful_actions": 0,
            "failed_actions": 0,
            "avg_confidence": 0.0
        }

    def evaluate_decision(
        self,
        context: Dict[str, Any],
        proposed_action: str,
        alternatives: List[str]
    ) -> Decision:
        """Evaluate and make a decision"""
        if self.logger:
            self.logger.log("autonomy_evaluate", {
                "action": proposed_action,
                "alternatives": len(alternatives)
            })

        # Analyze context
        reasoning = []
        confidence = 0.5

        # Check if action aligns with goals
        if "issue" in context:
            reasoning.append("Issue context provided")
            confidence += 0.1

        if "research" in context:
            reasoning.append("Research data available")
            confidence += 0.15

        # Evaluate alternatives
        if len(alternatives) > 0:
            reasoning.append(f"Considered {len(alternatives)} alternatives")
            confidence += 0.1

        # Check historical success rate
        if self.performance_metrics["decisions_made"] > 0:
            success_rate = (
                self.performance_metrics["successful_actions"] /
                max(1, self.performance_metrics["decisions_made"])
            )
            if success_rate > 0.7:
                confidence += 0.15
                reasoning.append("High historical success rate")

        # Normalize confidence
        confidence = min(1.0, confidence)

        decision = Decision(
            decision_id=f"dec_{int(time.time())}",
            decision_type=proposed_action,
            confidence=confidence,
            reasoning=reasoning,
            actions=[]
        )

        self.decision_history.append(decision)
        self.performance_metrics["decisions_made"] += 1
        self.performance_metrics["avg_confidence"] = (
            (self.performance_metrics["avg_confidence"] * (len(self.decision_history) - 1) + confidence) /
            len(self.decision_history)
        )

        return decision

    def reflect_on_outcome(self, decision_id: str, success: bool):
        """Reflect on the outcome of a decision"""
        if success:
            self.performance_metrics["successful_actions"] += 1
        else:
            self.performance_metrics["failed_actions"] += 1

        if self.logger:
            self.logger.log("autonomy_reflect", {
                "decision": decision_id,
                "success": success,
                "success_rate": self.get_success_rate()
            })

    def get_success_rate(self) -> float:
        """Get current success rate"""
        total = self.performance_metrics["successful_actions"] + self.performance_metrics["failed_actions"]
        if total == 0:
            return 0.0
        return self.performance_metrics["successful_actions"] / total

    def should_act(self, confidence_threshold: float = 0.6) -> bool:
        """Determine if confidence is high enough to act"""
        return self.performance_metrics.get("avg_confidence", 0) >= confidence_threshold


class DeepCausalityEngine:
    """
    Deep Causality Engine
    - Analyzes root causes
    - Predicts outcomes
    - Maps causal relationships
    """

    def __init__(self, logger=None):
        self.logger = logger

    def analyze_causality(
        self,
        issue_context: Dict[str, Any],
        research_data: Dict[str, Any]
    ) -> CausalityChain:
        """Analyze deep causality of an issue or situation"""
        if self.logger:
            self.logger.log("causality_analyze", {
                "context_keys": list(issue_context.keys())
            })

        # Identify root cause
        root_cause = self._identify_root_cause(issue_context, research_data)

        # Find contributing factors
        factors = self._find_contributing_factors(issue_context, research_data)

        # Predict outcomes
        outcomes = self._predict_outcomes(root_cause, factors)

        # Calculate confidence
        confidence = self._calculate_causality_confidence(root_cause, factors, outcomes)

        chain = CausalityChain(
            root_cause=root_cause,
            contributing_factors=factors,
            expected_outcomes=outcomes,
            confidence=confidence
        )

        return chain

    def _identify_root_cause(self, context: Dict[str, Any], research: Dict[str, Any]) -> str:
        """Identify the root cause"""
        # Simplified root cause analysis
        if "problem" in context:
            return context["problem"]

        if "patterns" in research:
            patterns = research.get("patterns", [])
            if patterns:
                return f"Pattern identified: {patterns[0]}"

        return "Need for improvement identified"

    def _find_contributing_factors(self, context: Dict[str, Any], research: Dict[str, Any]) -> List[str]:
        """Find contributing factors"""
        factors = []

        if "patterns" in research:
            factors.extend(research["patterns"][:3])

        if "similar_issues" in research:
            factors.append(f"{len(research['similar_issues'])} similar issues found")

        if not factors:
            factors.append("General system improvement opportunity")

        return factors

    def _predict_outcomes(self, root_cause: str, factors: List[str]) -> List[str]:
        """Predict expected outcomes"""
        outcomes = [
            "Improved system functionality",
            "Better code maintainability",
            "Enhanced user experience"
        ]

        if "automation" in root_cause.lower():
            outcomes.append("Increased automation efficiency")

        if factors:
            outcomes.append("Resolution of identified patterns")

        return outcomes

    def _calculate_causality_confidence(
        self,
        root_cause: str,
        factors: List[str],
        outcomes: List[str]
    ) -> float:
        """Calculate confidence in causality analysis"""
        confidence = 0.5

        if root_cause and len(root_cause) > 10:
            confidence += 0.15

        if len(factors) >= 2:
            confidence += 0.2

        if len(outcomes) >= 3:
            confidence += 0.15

        return min(1.0, confidence)


class AKSIOrchestrator:
    """
    Main orchestrator coordinating all agents
    Uses Reflective Autonomy v2 + Deep Causality Engine
    """

    def __init__(self, logger=None):
        self.logger = logger

        # Initialize agents
        self.researcher = AIResearcher(logger)
        self.writer = AIWriter(logger)
        self.validator = AIValidator(logger)
        self.integrator = AIIntegrator(logger)

        # Initialize engines
        self.autonomy = ReflectiveAutonomyEngine(logger)
        self.causality = DeepCausalityEngine(logger)

        # Track tasks
        self.active_tasks = {}
        self.stats = {
            "issues_created": 0,
            "issues_updated": 0,
            "issues_closed": 0,
            "prs_created": 0,
            "analyses_performed": 0
        }

    def analyze_and_act(
        self,
        repository: str,
        issue_number: Optional[int] = None,
        action: str = "analyze",
        task_id: str = None
    ):
        """Main workflow: analyze repository and take action"""
        if self.logger:
            self.logger.log("orchestrator_start", {
                "repository": repository,
                "action": action,
                "task_id": task_id
            })

        # Update task status
        if task_id:
            self.active_tasks[task_id] = {
                "status": "running",
                "started_at": time.time(),
                "repository": repository,
                "action": action
            }

        try:
            # Step 1: Research
            research_result = self.researcher.analyze_repository(repository)
            self.stats["analyses_performed"] += 1

            # Step 2: Causality analysis
            causality = self.causality.analyze_causality(
                issue_context={"repository": repository},
                research_data={
                    "patterns": research_result.patterns,
                    "similar_issues": research_result.similar_issues
                }
            )

            # Step 3: Decision making
            decision = self.autonomy.evaluate_decision(
                context={
                    "repository": repository,
                    "research": research_result,
                    "causality": causality
                },
                proposed_action=action,
                alternatives=["analyze", "create", "update"]
            )

            # Step 4: Execute action if confidence is high enough
            result = None
            if decision.confidence >= 0.6:
                if action == "create":
                    result = self._create_issue_workflow(repository, research_result, causality)
                elif action == "update" and issue_number:
                    result = self._update_issue_workflow(repository, issue_number, research_result)
                elif action == "analyze":
                    result = {
                        "research": research_result,
                        "causality": causality,
                        "decision": decision
                    }

                self.autonomy.reflect_on_outcome(decision.decision_id, success=True)
            else:
                result = {"message": "Confidence too low to act", "decision": decision}

            # Update task status
            if task_id:
                self.active_tasks[task_id] = {
                    "status": "completed",
                    "completed_at": time.time(),
                    "result": result
                }

            if self.logger:
                self.logger.log("orchestrator_complete", {
                    "task_id": task_id,
                    "action": action,
                    "confidence": decision.confidence
                })

        except Exception as e:
            if task_id:
                self.active_tasks[task_id] = {
                    "status": "failed",
                    "error": str(e)
                }

            if self.logger:
                self.logger.log("orchestrator_error", {
                    "task_id": task_id,
                    "error": str(e)
                }, level="ERROR")

    def _create_issue_workflow(
        self,
        repository: str,
        research_result,
        causality: CausalityChain
    ) -> Dict[str, Any]:
        """Workflow for creating a new issue"""
        # Generate issue variants
        variants = self.writer.generate_issue_variants(
            topic=causality.root_cause,
            context={
                "patterns": research_result.patterns,
                "recommendations": research_result.recommendations
            },
            num_variants=3
        )

        # Validate best variant
        best_variant = variants[0]
        validation = self.validator.validate_issue(
            title=best_variant.title,
            body=best_variant.body,
            labels=best_variant.labels
        )

        if validation.is_valid:
            # Queue for creation
            action = self.integrator.create_issue(
                repository=repository,
                title=best_variant.title,
                body=best_variant.body,
                labels=best_variant.labels
            )

            self.stats["issues_created"] += 1

            return {
                "action": "issue_created",
                "variant": best_variant,
                "validation": validation,
                "queued_action": action
            }
        else:
            return {
                "action": "validation_failed",
                "errors": validation.errors,
                "variant": best_variant
            }

    def _update_issue_workflow(
        self,
        repository: str,
        issue_number: int,
        research_result
    ) -> Dict[str, Any]:
        """Workflow for updating an existing issue"""
        # Generate progress comment
        comment = self.integrator.generate_progress_comment(
            status="analyzed",
            metrics={
                "Patterns Found": len(research_result.patterns),
                "Similar Issues": len(research_result.similar_issues),
                "Recommendations": len(research_result.recommendations)
            }
        )

        # Queue comment
        action = self.integrator.add_comment(
            repository=repository,
            issue_number=issue_number,
            comment=comment
        )

        self.stats["issues_updated"] += 1

        return {
            "action": "issue_updated",
            "comment": comment,
            "queued_action": action
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            **self.stats,
            "autonomy_metrics": self.autonomy.performance_metrics,
            "active_tasks": len([t for t in self.active_tasks.values() if t.get("status") == "running"])
        }

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task"""
        return self.active_tasks.get(task_id, {"status": "not_found"})

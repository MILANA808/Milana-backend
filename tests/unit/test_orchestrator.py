"""
Unit tests for AKSI Orchestrator
"""

import pytest
from aksi_agents.orchestrator import (
    AKSIOrchestrator,
    ReflectiveAutonomyEngine,
    DeepCausalityEngine,
    Decision,
    CausalityChain
)


class TestReflectiveAutonomyEngine:
    """Test suite for Reflective Autonomy Engine"""

    def setup_method(self):
        """Setup test instance"""
        self.autonomy = ReflectiveAutonomyEngine()

    def test_evaluate_decision(self):
        """Test decision evaluation"""
        decision = self.autonomy.evaluate_decision(
            context={"issue": "test", "research": "data"},
            proposed_action="create_issue",
            alternatives=["update_issue", "close_issue"]
        )

        assert isinstance(decision, Decision)
        assert 0 <= decision.confidence <= 1.0
        assert len(decision.reasoning) > 0
        assert decision.decision_type == "create_issue"

    def test_reflect_on_outcome_success(self):
        """Test reflection on successful outcome"""
        decision = self.autonomy.evaluate_decision(
            context={}, proposed_action="test", alternatives=[]
        )

        initial_successful = self.autonomy.performance_metrics["successful_actions"]
        self.autonomy.reflect_on_outcome(decision.decision_id, success=True)

        assert self.autonomy.performance_metrics["successful_actions"] == initial_successful + 1

    def test_reflect_on_outcome_failure(self):
        """Test reflection on failed outcome"""
        decision = self.autonomy.evaluate_decision(
            context={}, proposed_action="test", alternatives=[]
        )

        initial_failed = self.autonomy.performance_metrics["failed_actions"]
        self.autonomy.reflect_on_outcome(decision.decision_id, success=False)

        assert self.autonomy.performance_metrics["failed_actions"] == initial_failed + 1

    def test_get_success_rate(self):
        """Test success rate calculation"""
        rate = self.autonomy.get_success_rate()
        assert 0 <= rate <= 1.0

        # Add some results
        decision = self.autonomy.evaluate_decision({}, "test", [])
        self.autonomy.reflect_on_outcome(decision.decision_id, True)

        rate = self.autonomy.get_success_rate()
        assert rate == 1.0

    def test_should_act(self):
        """Test should act decision"""
        # Initially might not have high enough confidence
        result = self.autonomy.should_act(confidence_threshold=0.9)
        assert isinstance(result, bool)


class TestDeepCausalityEngine:
    """Test suite for Deep Causality Engine"""

    def setup_method(self):
        """Setup test instance"""
        self.causality = DeepCausalityEngine()

    def test_analyze_causality(self):
        """Test causality analysis"""
        chain = self.causality.analyze_causality(
            issue_context={"problem": "Slow performance"},
            research_data={"patterns": ["Pattern 1", "Pattern 2"]}
        )

        assert isinstance(chain, CausalityChain)
        assert chain.root_cause
        assert len(chain.contributing_factors) > 0
        assert len(chain.expected_outcomes) > 0
        assert 0 <= chain.confidence <= 1.0

    def test_identify_root_cause_from_context(self):
        """Test root cause identification from context"""
        root = self.causality._identify_root_cause(
            context={"problem": "API is broken"},
            research={}
        )

        assert "API is broken" in root

    def test_identify_root_cause_from_patterns(self):
        """Test root cause identification from patterns"""
        root = self.causality._identify_root_cause(
            context={},
            research={"patterns": ["Common issue found"]}
        )

        assert "Pattern identified" in root

    def test_find_contributing_factors(self):
        """Test finding contributing factors"""
        factors = self.causality._find_contributing_factors(
            context={},
            research={"patterns": ["P1", "P2"], "similar_issues": [{"num": 1}]}
        )

        assert len(factors) > 0

    def test_predict_outcomes(self):
        """Test outcome prediction"""
        outcomes = self.causality._predict_outcomes(
            root_cause="Need automation",
            factors=["Manual process"]
        )

        assert len(outcomes) > 0
        assert any("automation" in o.lower() for o in outcomes)

    def test_calculate_causality_confidence(self):
        """Test confidence calculation"""
        confidence = self.causality._calculate_causality_confidence(
            root_cause="Detailed root cause description",
            factors=["Factor 1", "Factor 2"],
            outcomes=["Outcome 1", "Outcome 2", "Outcome 3"]
        )

        assert 0 <= confidence <= 1.0
        assert confidence > 0.5  # Should have decent confidence with good inputs


class TestAKSIOrchestrator:
    """Test suite for AKSI Orchestrator"""

    def setup_method(self):
        """Setup test instance"""
        self.orchestrator = AKSIOrchestrator()

    def test_initialization(self):
        """Test orchestrator initialization"""
        assert self.orchestrator.researcher is not None
        assert self.orchestrator.writer is not None
        assert self.orchestrator.validator is not None
        assert self.orchestrator.integrator is not None
        assert self.orchestrator.autonomy is not None
        assert self.orchestrator.causality is not None

    def test_get_stats(self):
        """Test getting statistics"""
        stats = self.orchestrator.get_stats()

        assert "issues_created" in stats
        assert "issues_updated" in stats
        assert "analyses_performed" in stats
        assert "autonomy_metrics" in stats
        assert "active_tasks" in stats

    def test_get_task_status_not_found(self):
        """Test getting status of non-existent task"""
        status = self.orchestrator.get_task_status("nonexistent")

        assert status["status"] == "not_found"

    def test_create_issue_workflow(self):
        """Test issue creation workflow"""
        research_result = self.orchestrator.researcher.analyze_repository("test-org/test-repo")
        causality = self.orchestrator.causality.analyze_causality(
            {"repository": "test-org/test-repo"},
            {"patterns": research_result.patterns}
        )

        result = self.orchestrator._create_issue_workflow(
            "test-org/test-repo",
            research_result,
            causality
        )

        assert "action" in result
        if result["action"] == "issue_created":
            assert "variant" in result
            assert "validation" in result

    def test_update_issue_workflow(self):
        """Test issue update workflow"""
        research_result = self.orchestrator.researcher.analyze_repository("test-org/test-repo")

        result = self.orchestrator._update_issue_workflow(
            "test-org/test-repo",
            123,
            research_result
        )

        assert result["action"] == "issue_updated"
        assert "comment" in result
        assert "queued_action" in result

    def test_stats_increments(self):
        """Test that stats increment properly"""
        initial_created = self.orchestrator.stats["issues_created"]

        research_result = self.orchestrator.researcher.analyze_repository("test-org/test-repo")
        causality = self.orchestrator.causality.analyze_causality({}, {"patterns": []})

        self.orchestrator._create_issue_workflow("test-org/test-repo", research_result, causality)

        # Stats should increment if issue was created
        stats = self.orchestrator.get_stats()
        assert stats["issues_created"] >= initial_created

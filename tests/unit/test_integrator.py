"""
Unit tests for AI-Integrator agent
"""

import pytest
from aksi_agents.integrator import AIIntegrator, IntegrationAction


class TestAIIntegrator:
    """Test suite for AIIntegrator"""

    def setup_method(self):
        """Setup test instance"""
        self.integrator = AIIntegrator()

    def test_create_issue(self):
        """Test issue creation action"""
        action = self.integrator.create_issue(
            repository="test-org/test-repo",
            title="Test issue",
            body="Test body",
            labels=["enhancement"]
        )

        assert isinstance(action, IntegrationAction)
        assert action.action_type == "create"
        assert action.target_type == "issue"
        assert action.payload["title"] == "Test issue"
        assert action.status == "pending"

    def test_update_issue(self):
        """Test issue update action"""
        action = self.integrator.update_issue(
            repository="test-org/test-repo",
            issue_number=123,
            updates={"title": "New title"}
        )

        assert action.action_type == "update"
        assert action.target_id == 123
        assert "title" in action.payload

    def test_close_issue(self):
        """Test issue close action"""
        action = self.integrator.close_issue(
            repository="test-org/test-repo",
            issue_number=456,
            reason="completed"
        )

        assert action.action_type == "close"
        assert action.target_id == 456
        assert action.payload["reason"] == "completed"

    def test_add_comment(self):
        """Test adding comment"""
        action = self.integrator.add_comment(
            repository="test-org/test-repo",
            issue_number=789,
            comment="Test comment"
        )

        assert action.action_type == "comment"
        assert action.target_id == 789
        assert action.payload["body"] == "Test comment"

    def test_update_labels(self):
        """Test label update"""
        action = self.integrator.update_labels(
            repository="test-org/test-repo",
            issue_number=111,
            labels=["bug", "priority"]
        )

        assert action.action_type == "label"
        assert "bug" in action.payload["labels"]

    def test_generate_progress_comment(self):
        """Test progress comment generation"""
        comment = self.integrator.generate_progress_comment(
            status="in_progress",
            metrics={"tests": 10, "coverage": "85%"}
        )

        assert "AKSI Auto-Update" in comment
        assert "in_progress" in comment
        assert "tests" in comment.lower()

    def test_check_auto_close_conditions_closed(self):
        """Test auto-close check for already closed issue"""
        issue = {"number": 1, "state": "closed"}
        prs = []

        should_close = self.integrator.check_auto_close_conditions(issue, prs)

        assert not should_close

    def test_check_auto_close_conditions_merged_pr(self):
        """Test auto-close check with merged PR"""
        issue = {"number": 123, "state": "open"}
        prs = [
            {
                "state": "merged",
                "body": "This fixes #123 and resolves the issue"
            }
        ]

        should_close = self.integrator.check_auto_close_conditions(issue, prs)

        assert should_close

    def test_suggest_labels_feature(self):
        """Test label suggestion for feature"""
        labels = self.integrator.suggest_labels(
            issue_title="feat: add new feature",
            issue_body="Implement automation",
            existing_labels=[]
        )

        assert "enhancement" in labels

    def test_suggest_labels_bug(self):
        """Test label suggestion for bug"""
        labels = self.integrator.suggest_labels(
            issue_title="Fix broken API",
            issue_body="The API returns error 500",
            existing_labels=[]
        )

        assert "bug" in labels

    def test_suggest_labels_multiple(self):
        """Test label suggestion with multiple categories"""
        labels = self.integrator.suggest_labels(
            issue_title="Urgent: Add tests for critical feature",
            issue_body="Need testing automation",
            existing_labels=[]
        )

        assert "testing" in labels or "enhancement" in labels
        assert "priority" in labels

    def test_get_pending_actions(self):
        """Test getting pending actions"""
        self.integrator.create_issue("repo", "title", "body")
        self.integrator.add_comment("repo", 1, "comment")

        pending = self.integrator.get_pending_actions()

        assert len(pending) == 2
        assert all(a.status == "pending" for a in pending)

    def test_mark_action_completed(self):
        """Test marking action as completed"""
        action = self.integrator.create_issue("repo", "title", "body")
        assert action.status == "pending"

        self.integrator.mark_action_completed(action)
        assert action.status == "completed"

    def test_clear_completed_actions(self):
        """Test clearing completed actions"""
        action1 = self.integrator.create_issue("repo", "title1", "body1")
        action2 = self.integrator.create_issue("repo", "title2", "body2")

        self.integrator.mark_action_completed(action1)

        self.integrator.clear_completed_actions()

        remaining = self.integrator.action_queue
        assert len(remaining) == 1
        assert remaining[0].status == "pending"

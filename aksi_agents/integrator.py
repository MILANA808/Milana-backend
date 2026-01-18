"""
AI-Integrator Agent
Manages GitHub integration, updates issues, and handles automation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class IntegrationAction:
    """Action to be performed by integrator"""
    action_type: str  # create, update, close, comment, label
    target_type: str  # issue, pr
    target_id: Optional[int]
    payload: Dict[str, Any]
    status: str = "pending"


class AIIntegrator:
    """
    AI-Integrator Agent
    - Updates existing tickets
    - Adds progress comments
    - Manages labels and milestones
    - Closes resolved tickets
    """

    def __init__(self, logger=None):
        self.logger = logger
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.action_queue = []

    def create_issue(
        self,
        repository: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> IntegrationAction:
        """Create a new issue"""
        if self.logger:
            self.logger.log("integrator_create_issue", {
                "repo": repository,
                "title": title
            })

        action = IntegrationAction(
            action_type="create",
            target_type="issue",
            target_id=None,
            payload={
                "repository": repository,
                "title": title,
                "body": body,
                "labels": labels or [],
                "assignees": assignees or []
            }
        )

        self.action_queue.append(action)
        return action

    def update_issue(
        self,
        repository: str,
        issue_number: int,
        updates: Dict[str, Any]
    ) -> IntegrationAction:
        """Update an existing issue"""
        if self.logger:
            self.logger.log("integrator_update_issue", {
                "repo": repository,
                "issue": issue_number,
                "updates": list(updates.keys())
            })

        action = IntegrationAction(
            action_type="update",
            target_type="issue",
            target_id=issue_number,
            payload={
                "repository": repository,
                **updates
            }
        )

        self.action_queue.append(action)
        return action

    def close_issue(
        self,
        repository: str,
        issue_number: int,
        reason: str = "completed"
    ) -> IntegrationAction:
        """Close an issue"""
        if self.logger:
            self.logger.log("integrator_close_issue", {
                "repo": repository,
                "issue": issue_number,
                "reason": reason
            })

        action = IntegrationAction(
            action_type="close",
            target_type="issue",
            target_id=issue_number,
            payload={
                "repository": repository,
                "reason": reason,
                "state": "closed"
            }
        )

        self.action_queue.append(action)
        return action

    def add_comment(
        self,
        repository: str,
        issue_number: int,
        comment: str,
        target_type: str = "issue"
    ) -> IntegrationAction:
        """Add a comment to an issue or PR"""
        if self.logger:
            self.logger.log("integrator_add_comment", {
                "repo": repository,
                "target": issue_number,
                "type": target_type
            })

        action = IntegrationAction(
            action_type="comment",
            target_type=target_type,
            target_id=issue_number,
            payload={
                "repository": repository,
                "body": comment
            }
        )

        self.action_queue.append(action)
        return action

    def update_labels(
        self,
        repository: str,
        issue_number: int,
        labels: List[str],
        replace: bool = False
    ) -> IntegrationAction:
        """Update labels on an issue or PR"""
        if self.logger:
            self.logger.log("integrator_update_labels", {
                "repo": repository,
                "issue": issue_number,
                "labels": labels,
                "replace": replace
            })

        action = IntegrationAction(
            action_type="label",
            target_type="issue",
            target_id=issue_number,
            payload={
                "repository": repository,
                "labels": labels,
                "replace": replace
            }
        )

        self.action_queue.append(action)
        return action

    def generate_progress_comment(
        self,
        status: str,
        metrics: Dict[str, Any]
    ) -> str:
        """Generate a progress comment"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        comment = f"""## 🤖 AKSI Auto-Update

**Status:** {status}
**Updated:** {timestamp}

### Metrics
"""
        for key, value in metrics.items():
            comment += f"- **{key}:** {value}\n"

        comment += "\n---\n*This comment was automatically generated by AKSI*"

        return comment

    def check_auto_close_conditions(
        self,
        issue: Dict[str, Any],
        prs: List[Dict[str, Any]]
    ) -> bool:
        """Check if an issue should be auto-closed"""
        # Check if issue is already closed
        if issue.get("state") == "closed":
            return False

        # Check for linked merged PRs
        issue_number = issue.get("number")
        for pr in prs:
            if pr.get("state") == "merged":
                pr_body = pr.get("body", "")
                # Check if PR references this issue
                if f"#{issue_number}" in pr_body or f"fixes #{issue_number}" in pr_body.lower():
                    return True

        # Check for stale issues (placeholder for more complex logic)
        # Could check last activity date, labels, etc.

        return False

    def suggest_labels(
        self,
        issue_title: str,
        issue_body: str,
        existing_labels: List[str]
    ) -> List[str]:
        """Suggest labels based on content"""
        suggested = set(existing_labels)

        title_body = (issue_title + " " + issue_body).lower()

        # Feature detection
        if any(word in title_body for word in ["feat", "feature", "add", "implement"]):
            suggested.add("enhancement")

        # Bug detection
        if any(word in title_body for word in ["bug", "fix", "error", "broken"]):
            suggested.add("bug")

        # Documentation
        if any(word in title_body for word in ["doc", "documentation", "readme"]):
            suggested.add("documentation")

        # Testing
        if any(word in title_body for word in ["test", "testing", "coverage"]):
            suggested.add("testing")

        # Priority
        if any(word in title_body for word in ["urgent", "critical", "important"]):
            suggested.add("priority")

        # Automation
        if any(word in title_body for word in ["automat", "ci", "cd", "pipeline"]):
            suggested.add("automation")

        return list(suggested)

    def get_pending_actions(self) -> List[IntegrationAction]:
        """Get all pending actions"""
        return [a for a in self.action_queue if a.status == "pending"]

    def mark_action_completed(self, action: IntegrationAction):
        """Mark an action as completed"""
        action.status = "completed"
        if self.logger:
            self.logger.log("integrator_action_completed", {
                "action": action.action_type,
                "target": action.target_id
            })

    def clear_completed_actions(self):
        """Remove completed actions from queue"""
        self.action_queue = [a for a in self.action_queue if a.status != "completed"]

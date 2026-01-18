#!/usr/bin/env python3
"""
Auto Triage Script - Automatically label and triage new issues
"""

import os
import sys
import argparse
import re
from datetime import datetime

try:
    from github import Github
except ImportError:
    import subprocess
    print("Installing PyGithub...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyGithub"])
    from github import Github


class AutoTriage:
    """Automatically triage and label new issues"""

    def __init__(self, repo_name: str):
        self.token = os.environ.get("AKSI_PAT") or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("No GitHub token found")

        self.gh = Github(self.token)
        self.repo = self.gh.get_repo(repo_name)

    def triage_issue(self, issue_number: int, title: str, body: str) -> bool:
        """Triage a new issue and add appropriate labels"""
        try:
            issue = self.repo.get_issue(issue_number)
            labels_to_add = []

            # Analyze title and body for keywords
            text = f"{title} {body}".lower()

            # Bug detection
            if any(word in text for word in ["bug", "error", "crash", "fail", "broken", "issue"]):
                labels_to_add.append("bug")

            # Feature request detection
            if any(word in text for word in ["feature", "enhancement", "add", "implement", "support"]):
                labels_to_add.append("enhancement")

            # Documentation detection
            if any(word in text for word in ["documentation", "docs", "readme", "guide", "tutorial"]):
                labels_to_add.append("documentation")

            # Question detection
            if any(word in text for word in ["question", "how to", "help", "?", "asking"]):
                labels_to_add.append("question")

            # Priority detection
            if any(word in text for word in ["urgent", "critical", "asap", "important", "priority"]):
                labels_to_add.append("priority: high")

            # Add labels if any were detected
            if labels_to_add:
                # Get existing labels in the repo
                existing_labels = {label.name for label in self.repo.get_labels()}

                # Create missing labels
                for label_name in labels_to_add:
                    if label_name not in existing_labels:
                        self._create_label(label_name)

                # Add labels to issue
                issue.add_to_labels(*labels_to_add)
                print(f"✅ Added labels to issue #{issue_number}: {', '.join(labels_to_add)}")

            # Add a welcome comment
            welcome_comment = """👋 Thank you for opening this issue!

The AKSI bot has automatically triaged this issue. A maintainer will review it soon.

**Available commands:**
- `/aksi help` - Get help on using AKSI bot
- `/aksi status` - Check bot status
- `/solve <issue_url>` - Request automated solution

For support, contact: 716elektrik@mail.ru
"""
            issue.create_comment(welcome_comment)
            print(f"✅ Posted welcome comment to issue #{issue_number}")

            return True

        except Exception as e:
            print(f"❌ Error triaging issue: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_label(self, name: str) -> None:
        """Create a label if it doesn't exist"""
        # Color mapping for common labels
        colors = {
            "bug": "d73a4a",
            "enhancement": "a2eeef",
            "documentation": "0075ca",
            "question": "d876e3",
            "priority: high": "b60205",
        }

        color = colors.get(name, "ededed")

        try:
            self.repo.create_label(name, color)
            print(f"✅ Created label: {name}")
        except Exception as e:
            print(f"⚠️ Could not create label {name}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Auto Triage - Automatically label new issues")
    parser.add_argument("--repo", required=True, help="Repository in format owner/repo")
    parser.add_argument("--issue-number", type=int, required=True, help="Issue number")
    parser.add_argument("--issue-title", required=True, help="Issue title")
    parser.add_argument("--issue-body", default="", help="Issue body")

    args = parser.parse_args()

    try:
        triage = AutoTriage(args.repo)
        success = triage.triage_issue(args.issue_number, args.issue_title, args.issue_body)
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

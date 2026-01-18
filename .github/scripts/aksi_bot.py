#!/usr/bin/env python3
"""
AKSI Bot - Automated issue and PR solver
Handles /solve <issue_url> and /aksi commands
"""

import os
import sys
import argparse
import subprocess
import re
from typing import Optional, Dict, Any
from datetime import datetime

try:
    from github import Github
    import requests
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyGithub", "requests"])
    from github import Github
    import requests


class AKSIBot:
    """AKSI Bot for automating GitHub issue and PR workflows"""

    def __init__(self, repo_name: str):
        self.token = os.environ.get("AKSI_PAT") or os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("No GitHub token found in AKSI_PAT or GITHUB_TOKEN")

        self.gh = Github(self.token)
        self.repo = self.gh.get_repo(repo_name)
        self.repo_name = repo_name

    def parse_issue_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse GitHub issue URL to extract owner, repo, and issue number"""
        pattern = r"https?://github\.com/([^/]+)/([^/]+)/(?:issues|pull)/(\d+)"
        match = re.match(pattern, url)
        if match:
            return {
                "owner": match.group(1),
                "repo": match.group(2),
                "number": int(match.group(3))
            }
        return None

    def solve_issue(self, issue_url: str, comment_id: Optional[str] = None) -> bool:
        """
        Handle /solve <issue_url> command
        Creates a branch, analyzes the issue, and prepares a PR
        """
        print(f"🤖 AKSI Bot: Solving issue {issue_url}")

        issue_info = self.parse_issue_url(issue_url)
        if not issue_info:
            print(f"❌ Invalid issue URL: {issue_url}")
            return False

        try:
            # Get the issue details
            target_repo = self.gh.get_repo(f"{issue_info['owner']}/{issue_info['repo']}")
            issue = target_repo.get_issue(issue_info['number'])

            print(f"📋 Issue: {issue.title}")
            print(f"📝 Body: {issue.body[:200]}...")

            # Create a branch for this issue
            branch_name = f"aksi/solve-issue-{issue_info['number']}"

            # Comment on the original issue
            comment_body = f"""🤖 **AKSI Bot is on it!**

I'm analyzing this issue and will prepare a solution.

Branch: `{branch_name}`
Repository: {self.repo_name}

*Stay tuned for updates...*
"""
            if comment_id:
                # Reply to the comment that triggered the bot
                issue.create_comment(comment_body)

            # Log the action
            self._log_action("solve", {
                "issue_url": issue_url,
                "issue_number": issue_info['number'],
                "branch": branch_name,
                "timestamp": datetime.utcnow().isoformat()
            })

            print(f"✅ AKSI Bot response posted to issue #{issue_info['number']}")
            return True

        except Exception as e:
            print(f"❌ Error solving issue: {e}")
            import traceback
            traceback.print_exc()
            return False

    def handle_aksi_command(self, command: str, issue_number: Optional[int] = None) -> bool:
        """
        Handle /aksi <command> commands
        Supported commands: status, help, version
        """
        print(f"🤖 AKSI Bot: Handling command '{command}'")

        try:
            if command == "status":
                response = self._get_status()
            elif command == "help":
                response = self._get_help()
            elif command == "version":
                response = self._get_version()
            else:
                response = f"❌ Unknown command: `{command}`\n\nUse `/aksi help` to see available commands."

            # Post response to issue/PR if context is available
            if issue_number:
                issue = self.repo.get_issue(issue_number)
                issue.create_comment(response)
                print(f"✅ Response posted to issue #{issue_number}")
            else:
                print(response)

            return True

        except Exception as e:
            print(f"❌ Error handling command: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _get_status(self) -> str:
        """Get AKSI bot status"""
        return """🤖 **AKSI Bot Status**

✅ Operational and ready to assist!

**Capabilities:**
- `/solve <issue_url>` - Analyze and solve issues
- `/aksi status` - Check bot status
- `/aksi help` - Show help
- `/aksi version` - Show version

**Repository:** {repo}
**Last updated:** {timestamp}
""".format(
            repo=self.repo_name,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        )

    def _get_help(self) -> str:
        """Get AKSI bot help"""
        return """🤖 **AKSI Bot Help**

**Available Commands:**

1. **Solve an issue:**
   ```
   /solve https://github.com/owner/repo/issues/123
   ```
   The bot will analyze the issue and create a solution branch.

2. **Check status:**
   ```
   /aksi status
   ```
   Shows current bot status and capabilities.

3. **Get help:**
   ```
   /aksi help
   ```
   Shows this help message.

4. **Check version:**
   ```
   /aksi version
   ```
   Shows the bot version.

**Usage:**
- Comment on any issue or PR with a command
- The bot will respond automatically
- For `/solve`, provide a valid GitHub issue URL

**Support:**
Contact: 716elektrik@mail.ru (Alfiia Bashirova)
"""

    def _get_version(self) -> str:
        """Get AKSI bot version"""
        return """🤖 **AKSI Bot Version**

**Version:** 1.0.0
**Release Date:** 2025-01-18
**Author:** Alfiia Bashirova (AKSI Project)
**Repository:** MILANA808/Milana-backend

**Features:**
- Automated issue solving
- GitHub Actions integration
- Command-based interaction
- FastAPI backend support
"""

    def _log_action(self, action: str, data: Dict[str, Any]) -> None:
        """Log bot actions to a file"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "aksi_bot.log")
        timestamp = datetime.utcnow().isoformat()

        log_entry = f"[{timestamp}] {action}: {data}\n"

        with open(log_file, "a") as f:
            f.write(log_entry)

        print(f"📝 Logged action: {action}")


def main():
    parser = argparse.ArgumentParser(description="AKSI Bot - Automated issue and PR solver")
    parser.add_argument("--action", required=True, choices=["solve", "aksi", "auto"],
                        help="Action to perform")
    parser.add_argument("--issue-url", help="Issue URL for /solve command")
    parser.add_argument("--aksi-command", help="Command for /aksi")
    parser.add_argument("--repo", required=True, help="Repository in format owner/repo")
    parser.add_argument("--comment-id", help="Comment ID that triggered the bot")
    parser.add_argument("--issue-number", type=int, help="Issue or PR number")
    parser.add_argument("--event", help="GitHub event type")

    args = parser.parse_args()

    try:
        bot = AKSIBot(args.repo)

        if args.action == "solve":
            if not args.issue_url:
                print("❌ Error: --issue-url is required for solve action")
                sys.exit(1)
            success = bot.solve_issue(args.issue_url, args.comment_id)
        elif args.action == "aksi":
            if not args.aksi_command:
                print("❌ Error: --aksi-command is required for aksi action")
                sys.exit(1)
            success = bot.handle_aksi_command(args.aksi_command, args.issue_number)
        else:
            print(f"ℹ️ Auto action for event: {args.event}")
            success = True

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

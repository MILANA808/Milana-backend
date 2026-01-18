"""
AI-Validator Agent
Validates PRs for conflicts, duplicates, and format errors
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    """Result from validation check"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    score: float  # 0.0 - 1.0


class AIValidator:
    """
    AI-Validator Agent
    - Checks for PR conflicts
    - Detects duplicate issues
    - Validates markdown format
    - Simulates PR impact
    """

    def __init__(self, logger=None):
        self.logger = logger

    def validate_issue(
        self,
        title: str,
        body: str,
        labels: List[str],
        existing_issues: Optional[List[Dict[str, Any]]] = None
    ) -> ValidationResult:
        """Validate an issue before creation"""
        if self.logger:
            self.logger.log("validator_issue", {"title": title})

        errors = []
        warnings = []
        suggestions = []

        # Check title
        if len(title) < 10:
            errors.append("Title too short (minimum 10 characters)")
        if len(title) > 200:
            warnings.append("Title is very long (consider shortening)")

        # Check body
        if len(body) < 30:
            errors.append("Description too short (minimum 30 characters)")

        # Check markdown format
        markdown_errors = self._validate_markdown(body)
        errors.extend(markdown_errors)

        # Check for duplicates
        if existing_issues:
            is_duplicate, duplicate_num = self._check_duplicates(title, body, existing_issues)
            if is_duplicate:
                warnings.append(f"Possible duplicate of issue #{duplicate_num}")

        # Check labels
        if not labels:
            warnings.append("No labels specified - consider adding labels")

        # Generate suggestions
        if "test" not in body.lower() and "bug" not in labels:
            suggestions.append("Consider adding testing checklist")
        if "##" not in body:
            suggestions.append("Use markdown headers for better structure")

        # Calculate validation score
        score = self._calculate_validation_score(errors, warnings, len(body))

        is_valid = len(errors) == 0 and score >= 0.5

        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            score=score
        )

        if self.logger:
            self.logger.log("validator_result", {
                "valid": is_valid,
                "errors": len(errors),
                "warnings": len(warnings),
                "score": score
            })

        return result

    def validate_pr(
        self,
        title: str,
        body: str,
        files_changed: List[str],
        target_branch: str = "main"
    ) -> ValidationResult:
        """Validate a PR before creation"""
        if self.logger:
            self.logger.log("validator_pr", {
                "title": title,
                "files": len(files_changed)
            })

        errors = []
        warnings = []
        suggestions = []

        # Check PR title format
        if not self._check_pr_title_format(title):
            warnings.append("PR title doesn't follow conventional format (e.g., 'feat:', 'fix:')")

        # Check body
        if len(body) < 50:
            errors.append("PR description too short")

        if "fixes #" not in body.lower() and "closes #" not in body.lower():
            warnings.append("PR doesn't reference an issue")

        # Check files
        if not files_changed:
            errors.append("No files changed in PR")

        if len(files_changed) > 50:
            warnings.append("PR changes many files - consider splitting")

        # Check for test files
        has_tests = any("test" in f.lower() for f in files_changed)
        has_code = any(f.endswith(('.py', '.js', '.ts', '.go')) for f in files_changed)

        if has_code and not has_tests:
            suggestions.append("Consider adding tests for code changes")

        # Check markdown
        markdown_errors = self._validate_markdown(body)
        errors.extend(markdown_errors)

        # Calculate score
        score = self._calculate_validation_score(errors, warnings, len(body))
        is_valid = len(errors) == 0 and score >= 0.6

        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            score=score
        )

        if self.logger:
            self.logger.log("validator_pr_result", {
                "valid": is_valid,
                "score": score
            })

        return result

    def _validate_markdown(self, text: str) -> List[str]:
        """Validate markdown formatting"""
        errors = []

        # Check for unclosed code blocks
        code_blocks = re.findall(r'```', text)
        if len(code_blocks) % 2 != 0:
            errors.append("Unclosed code block detected")

        # Check for malformed links
        links = re.findall(r'\[([^\]]+)\]\(([^)]*)\)', text)
        for link_text, link_url in links:
            if not link_url:
                errors.append(f"Empty URL in link: [{link_text}]()")

        # Check for unclosed bold/italic
        bold_count = len(re.findall(r'\*\*', text))
        if bold_count % 2 != 0:
            errors.append("Unclosed bold marker (**)")

        return errors

    def _check_duplicates(
        self,
        title: str,
        body: str,
        existing_issues: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[int]]:
        """Check if issue is duplicate"""
        title_lower = title.lower()

        for issue in existing_issues:
            existing_title = issue.get("title", "").lower()

            # Simple similarity check
            if self._calculate_similarity(title_lower, existing_title) > 0.7:
                return True, issue.get("number")

        return False, None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (0.0 - 1.0)"""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _check_pr_title_format(self, title: str) -> bool:
        """Check if PR title follows conventional format"""
        patterns = [
            r'^feat:',
            r'^fix:',
            r'^docs:',
            r'^test:',
            r'^refactor:',
            r'^chore:',
            r'^style:',
            r'^perf:',
        ]

        return any(re.match(pattern, title, re.IGNORECASE) for pattern in patterns)

    def _calculate_validation_score(self, errors: List[str], warnings: List[str], content_length: int) -> float:
        """Calculate overall validation score"""
        score = 1.0

        # Deduct for errors
        score -= len(errors) * 0.2

        # Deduct for warnings (less severe)
        score -= len(warnings) * 0.05

        # Bonus for good content length
        if content_length > 100:
            score += 0.1

        return max(0.0, min(1.0, score))

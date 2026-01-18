"""
Unit tests for AI-Validator agent
"""

import pytest
from aksi_agents.validator import AIValidator, ValidationResult


class TestAIValidator:
    """Test suite for AIValidator"""

    def setup_method(self):
        """Setup test instance"""
        self.validator = AIValidator()

    def test_validate_issue_valid(self):
        """Test validation of valid issue"""
        result = self.validator.validate_issue(
            title="Add automation feature",
            body="## Problem\nManual process is slow\n## Solution\nAutomate the workflow",
            labels=["enhancement"]
        )

        assert isinstance(result, ValidationResult)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_issue_short_title(self):
        """Test validation with short title"""
        result = self.validator.validate_issue(
            title="Short",
            body="This is a valid body with enough content to pass validation",
            labels=[]
        )

        assert not result.is_valid
        assert any("Title too short" in e for e in result.errors)

    def test_validate_issue_short_body(self):
        """Test validation with short body"""
        result = self.validator.validate_issue(
            title="Valid title here",
            body="Short",
            labels=[]
        )

        assert not result.is_valid
        assert any("Description too short" in e for e in result.errors)

    def test_validate_markdown_unclosed_code(self):
        """Test markdown validation with unclosed code block"""
        errors = self.validator._validate_markdown("```python\ncode here")

        assert any("Unclosed code block" in e for e in errors)

    def test_validate_markdown_empty_link(self):
        """Test markdown validation with empty link"""
        errors = self.validator._validate_markdown("[click here]()")

        assert any("Empty URL" in e for e in errors)

    def test_validate_pr_valid(self):
        """Test PR validation with valid content"""
        result = self.validator.validate_pr(
            title="feat: add new feature",
            body="Fixes #123\n\nThis PR adds new functionality with tests",
            files_changed=["app.py", "test_app.py"]
        )

        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_pr_no_files(self):
        """Test PR validation with no files"""
        result = self.validator.validate_pr(
            title="feat: something",
            body="Description here with enough content to be valid",
            files_changed=[]
        )

        assert not result.is_valid
        assert any("No files changed" in e for e in result.errors)

    def test_validate_pr_no_issue_reference(self):
        """Test PR validation without issue reference"""
        result = self.validator.validate_pr(
            title="feat: add feature",
            body="This is a description without an issue reference but long enough",
            files_changed=["app.py"]
        )

        assert any("doesn't reference an issue" in w for w in result.warnings)

    def test_check_pr_title_format(self):
        """Test PR title format checking"""
        assert self.validator._check_pr_title_format("feat: add feature")
        assert self.validator._check_pr_title_format("fix: bug fix")
        assert not self.validator._check_pr_title_format("Add feature")

    def test_calculate_similarity(self):
        """Test text similarity calculation"""
        similarity = self.validator._calculate_similarity(
            "add automation feature",
            "add automation feature"
        )
        assert similarity == 1.0

        similarity = self.validator._calculate_similarity(
            "add automation",
            "implement automation system"
        )
        assert 0 < similarity < 1.0

    def test_check_duplicates(self):
        """Test duplicate detection"""
        existing = [
            {"number": 1, "title": "Add automation feature"},
            {"number": 2, "title": "Fix bug in API"}
        ]

        is_dup, num = self.validator._check_duplicates(
            "Add automation feature",
            "Body content",
            existing
        )

        assert is_dup
        assert num == 1

    def test_validation_score_calculation(self):
        """Test validation score calculation"""
        score = self.validator._calculate_validation_score(
            errors=[],
            warnings=[],
            content_length=200
        )

        assert score >= 1.0  # Should have bonus for good length (capped at 1.0)
        assert score == 1.0  # Max score is 1.0

        score_with_errors = self.validator._calculate_validation_score(
            errors=["Error 1"],
            warnings=["Warning 1"],
            content_length=50
        )

        assert score_with_errors < score

"""
Unit tests for AI-Writer agent
"""

import pytest
from aksi_agents.writer import AIWriter, WrittenContent


class TestAIWriter:
    """Test suite for AIWriter"""

    def setup_method(self):
        """Setup test instance"""
        self.writer = AIWriter()

    def test_generate_issue_variants(self):
        """Test issue variant generation"""
        variants = self.writer.generate_issue_variants(
            topic="Add automation feature",
            context={"problem": "Manual process", "solution": "Automate it"},
            num_variants=3
        )

        assert len(variants) == 3
        assert all(isinstance(v, WrittenContent) for v in variants)
        # Variants should be sorted by EQS score (highest first)
        assert variants[0].eqs_score >= variants[1].eqs_score
        assert variants[1].eqs_score >= variants[2].eqs_score

    def test_variant_structure(self):
        """Test variant has required fields"""
        variants = self.writer.generate_issue_variants(
            topic="Test feature",
            context={},
            num_variants=1
        )

        variant = variants[0]
        assert variant.variant_id
        assert variant.title
        assert variant.body
        assert isinstance(variant.labels, list)
        assert 0 <= variant.eqs_score <= 1.0
        assert isinstance(variant.metadata, dict)

    def test_suggest_labels(self):
        """Test label suggestion"""
        labels = self.writer._suggest_labels(
            topic="feat: add tests",
            context={"automation": True}
        )

        assert "enhancement" in labels or "testing" in labels

    def test_suggest_labels_bug(self):
        """Test bug label suggestion"""
        labels = self.writer._suggest_labels(
            topic="fix: broken API",
            context={}
        )

        assert "bug" in labels

    def test_calculate_eqs_score(self):
        """Test EQS score calculation"""
        score = self.writer._calculate_eqs_score(
            title="Implement feature X",
            body="## Problem\nCurrent issue\n## Solution\nProposed fix\n- [ ] Task 1",
            context={"patterns": ["Pattern 1"]}
        )

        assert 0 <= score <= 1.0
        assert score > 0.5  # Should have good score with structured content

    def test_generate_pr_description(self):
        """Test PR description generation"""
        description = self.writer.generate_pr_description(
            issue_number=123,
            changes=["Add new API endpoint", "Update tests"],
            context={"testing": "All tests pass"}
        )

        assert "Fixes #123" in description
        assert "Add new API endpoint" in description
        assert "Update tests" in description
        assert "Checklist" in description

    def test_detailed_body_generation(self):
        """Test detailed body generation"""
        body = self.writer._generate_detailed_body(
            topic="automation feature",
            context={"problem": "Manual work", "solution": "Automate it"}
        )

        assert "## Overview" in body
        assert "automation feature" in body

    def test_concise_body_generation(self):
        """Test concise body generation"""
        body = self.writer._generate_concise_body(
            topic="automation",
            context={"problem": "Manual"}
        )

        assert "Goal:" in body
        assert "[ ]" in body  # Has checklist

    def test_technical_body_generation(self):
        """Test technical body generation"""
        body = self.writer._generate_technical_body(
            topic="new API",
            context={"scope": "Backend"}
        )

        assert "Technical Specification" in body
        assert "Requirements:" in body

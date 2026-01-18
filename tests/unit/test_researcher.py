"""
Unit tests for AI-Researcher agent
"""

import pytest
from aksi_agents.researcher import AIResearcher, ResearchResult


class TestAIResearcher:
    """Test suite for AIResearcher"""

    def setup_method(self):
        """Setup test instance"""
        self.researcher = AIResearcher()

    def test_analyze_repository(self):
        """Test repository analysis"""
        result = self.researcher.analyze_repository("test-org/test-repo")

        assert isinstance(result, ResearchResult)
        assert result.repository == "test-org/test-repo"
        assert isinstance(result.similar_issues, list)
        assert isinstance(result.similar_prs, list)
        assert isinstance(result.patterns, list)
        assert isinstance(result.recommendations, list)

    def test_analyze_repository_with_topic(self):
        """Test repository analysis with topic"""
        result = self.researcher.analyze_repository("test-org/test-repo", topic="automation")

        assert result.metadata["topic"] == "automation"
        assert len(result.patterns) > 0

    def test_search_similar_repositories(self):
        """Test searching similar repositories"""
        results = self.researcher.search_similar_repositories(["automation", "github"], limit=3)

        assert isinstance(results, list)
        assert len(results) <= 3

    def test_find_similar_issues(self):
        """Test finding similar issues"""
        issues = self.researcher._find_similar_issues("test-org/test-repo", None)

        assert isinstance(issues, list)
        if issues:
            assert "number" in issues[0]
            assert "title" in issues[0]

    def test_extract_patterns(self):
        """Test pattern extraction"""
        issues = [{"title": "Add automation", "labels": ["enhancement"]}]
        prs = [{"title": "feat: add CI", "labels": ["feature"]}]

        patterns = self.researcher._extract_patterns(issues, prs)

        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_generate_recommendations(self):
        """Test recommendation generation"""
        patterns = ["Pattern 1", "Pattern 2"]
        recommendations = self.researcher._generate_recommendations(patterns)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("test" in r.lower() for r in recommendations)

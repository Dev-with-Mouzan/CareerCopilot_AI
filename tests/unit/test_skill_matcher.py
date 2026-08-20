"""Tests for backend.services.skill_matcher — deterministic skill matching."""

from __future__ import annotations

import pytest

from backend.services.skill_matcher import SkillMatchResult, match_skills


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def resume_skills():
    return ["python", "javascript", "react", "docker", "postgresql", "git"]


@pytest.fixture
def job_skills():
    return ["python", "react", "docker", "kubernetes", "aws", "graphql"]


# ── Basic Matching ────────────────────────────────────────────────────────────


class TestMatchSkillsBasic:
    def test_exact_matches(self, resume_skills, job_skills):
        result = match_skills(resume_skills, job_skills)
        assert isinstance(result, SkillMatchResult)
        assert "python" in result.exact_matches
        assert "react" in result.exact_matches
        assert "docker" in result.exact_matches

    def test_missing_skills(self, resume_skills, job_skills):
        result = match_skills(resume_skills, job_skills)
        assert "kubernetes" in result.job_only
        assert "aws" in result.job_only
        assert "graphql" in result.job_only

    def test_resume_only(self, resume_skills, job_skills):
        result = match_skills(resume_skills, job_skills)
        assert "javascript" in result.resume_only
        assert "postgresql" in result.resume_only
        assert "git" in result.resume_only

    def test_overlap_percentage(self, resume_skills, job_skills):
        result = match_skills(resume_skills, job_skills)
        # 3 exact out of 6 job skills = 50%
        assert result.overlap_percentage == 50.0

    def test_totals(self, resume_skills, job_skills):
        result = match_skills(resume_skills, job_skills)
        assert result.total_resume == 6
        assert result.total_job == 6


# ── Edge Cases ────────────────────────────────────────────────────────────────


class TestMatchSkillsEdgeCases:
    def test_empty_resume(self, job_skills):
        result = match_skills([], job_skills)
        assert result.exact_matches == []
        assert result.overlap_percentage == 0.0
        assert result.total_resume == 0

    def test_empty_job(self, resume_skills):
        result = match_skills(resume_skills, [])
        assert result.overlap_percentage == 100.0
        assert result.total_job == 0

    def test_both_empty(self):
        result = match_skills([], [])
        assert result.overlap_percentage == 100.0

    def test_perfect_match(self):
        skills = ["python", "react", "docker"]
        result = match_skills(skills, skills)
        assert result.overlap_percentage == 100.0
        assert len(result.exact_matches) == 3
        assert result.job_only == []

    def test_no_match(self):
        result = match_skills(["java", "spring"], ["python", "django"])
        assert result.overlap_percentage == 0.0
        assert result.exact_matches == []


# ── Alias / Normalization ────────────────────────────────────────────────────


class TestSkillNormalization:
    def test_alias_normalized(self):
        result = match_skills(["ReactJS"], ["react"])
        assert "react" in result.exact_matches

    def test_case_insensitive(self):
        result = match_skills(["Python", "JavaScript"], ["python", "javascript"])
        assert "python" in result.exact_matches
        assert "javascript" in result.exact_matches

    def test_partial_match_detected(self):
        result = match_skills(["react", "javascript"], ["react native"])
        assert len(result.partial_matches) >= 1

    def test_partial_match_substring(self):
        result = match_skills(["postgresql"], ["sql"])
        assert len(result.partial_matches) >= 1


# ── Result Counts ─────────────────────────────────────────────────────────────


class TestResultCounts:
    def test_sorted_output(self, resume_skills, job_skills):
        result = match_skills(resume_skills, job_skills)
        assert result.exact_matches == sorted(result.exact_matches)
        assert result.resume_only == sorted(result.resume_only)
        assert result.job_only == sorted(result.job_only)

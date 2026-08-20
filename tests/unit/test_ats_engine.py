"""Tests for backend.services.ats_engine — deterministic ATS scoring."""

from __future__ import annotations

from datetime import date

import pytest

from backend.core.schemas import (
    ATSReport,
    ContactInfo,
    Education,
    Experience,
    ResumeProfile,
    Skill,
    SkillCategory,
)
from backend.services.ats_engine import (
    _education_score,
    _experience_score,
    _extract_keywords,
    _extract_required_years,
    _format_score,
    _keyword_score,
    _skill_score,
    _tokenize,
    calculate_ats_score,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_resume_text():
    return (
        "John Doe is a senior software engineer with expertise in Python, JavaScript, "
        "React, and Docker. He has 6 years of experience building web applications. "
        "Education: B.S. in Computer Science from MIT."
    )


@pytest.fixture
def sample_job_description():
    return (
        "We are looking for a Senior Software Engineer with 5+ years of experience. "
        "Required skills: Python, JavaScript, React, Docker, Kubernetes, AWS, "
        "PostgreSQL, and CI/CD. Experience with microservices and agile methodology."
    )


@pytest.fixture
def sample_profile():
    return ResumeProfile(
        skills=[
            Skill(name="python", category=SkillCategory.technical),
            Skill(name="javascript", category=SkillCategory.technical),
            Skill(name="react", category=SkillCategory.technical),
            Skill(name="docker", category=SkillCategory.technical),
            Skill(name="postgresql", category=SkillCategory.technical),
        ],
        experience=[
            Experience(
                title="Software Engineer",
                company="TechCo",
                start_date=date(2020, 1, 1),
                end_date=date(2026, 1, 1),
                description="Built web apps with Python and React.",
                skills_used=["python", "react"],
            )
        ],
        education=[
            Education(
                institution="MIT",
                degree="Bachelor of Science in Computer Science",
                field="Computer Science",
                start_date=date(2016, 9, 1),
                end_date=date(2020, 6, 1),
                gpa=3.8,
            )
        ],
        years_experience=6.0,
        summary="Senior software engineer with 6 years of experience.",
        contact_info=ContactInfo(
            email="john@example.com",
            phone="+1 555 123 4567",
            linkedin="linkedin.com/in/johndoe",
        ),
    )


# ── Tokenization ──────────────────────────────────────────────────────────────


class TestTokenize:
    def test_basic(self):
        tokens = _tokenize("Python and JavaScript are great")
        assert "python" in tokens
        assert "javascript" in tokens
        assert "and" not in tokens  # stopword

    def test_empty(self):
        assert _tokenize("") == []

    def test_stopwords_removed(self):
        tokens = _tokenize("the quick brown fox")
        assert "the" not in tokens


# ── Keyword Extraction ────────────────────────────────────────────────────────


class TestExtractKeywords:
    def test_returns_list(self, sample_job_description):
        kw = _extract_keywords(sample_job_description)
        assert isinstance(kw, list)
        assert len(kw) > 0

    def test_top_n_limit(self, sample_job_description):
        kw = _extract_keywords(sample_job_description, top_n=5)
        assert len(kw) <= 5

    def test_empty_text(self):
        kw = _extract_keywords("")
        assert kw == []


# ── Keyword Score ─────────────────────────────────────────────────────────────


class TestKeywordScore:
    def test_full_match(self):
        score, missing = _keyword_score("python react docker", ["python", "react", "docker"])
        assert score == 100.0
        assert missing == []

    def test_partial_match(self):
        score, missing = _keyword_score("python react", ["python", "react", "docker"])
        assert 50.0 <= score < 100.0
        assert "docker" in missing

    def test_no_match(self):
        score, missing = _keyword_score("hello world", ["python", "react"])
        assert score == 0.0
        assert len(missing) == 2

    def test_empty_keywords(self):
        score, _ = _keyword_score("anything", [])
        assert score == 100.0


# ── Skill Score ───────────────────────────────────────────────────────────────


class TestSkillScore:
    def test_exact_match(self):
        score, missing = _skill_score(["python", "react"], ["python", "react"])
        assert score == 100.0
        assert missing == []

    def test_with_aliases(self):
        score, missing = _skill_score(["javascript", "reactjs"], ["js", "react"])
        assert score == 100.0

    def test_missing(self):
        score, missing = _skill_score(["python"], ["python", "kubernetes", "aws"])
        assert score < 100.0
        assert "kubernetes" in missing

    def test_empty_job_skills(self):
        score, _ = _skill_score(["python"], [])
        assert score == 100.0


# ── Experience Score ──────────────────────────────────────────────────────────


class TestExperienceScore:
    def test_meets_requirement(self, sample_profile):
        score = _experience_score(sample_profile, required_years=5.0)
        assert score == 100.0

    def test_below_requirement(self, sample_profile):
        score = _experience_score(sample_profile, required_years=10.0)
        assert 50.0 <= score < 100.0

    def test_zero_years(self):
        profile = ResumeProfile(years_experience=0.0)
        score = _experience_score(profile, required_years=3.0)
        assert score == 0.0


# ── Education Score ───────────────────────────────────────────────────────────


class TestEducationScore:
    def test_bachelor(self):
        profile = ResumeProfile(
            education=[Education(institution="MIT", degree="Bachelor of Science", field="CS")]
        )
        assert _education_score(profile) == 70.0

    def test_master(self):
        profile = ResumeProfile(
            education=[Education(institution="MIT", degree="Master of Science", field="CS")]
        )
        assert _education_score(profile) == 85.0

    def test_phd(self):
        profile = ResumeProfile(
            education=[Education(institution="MIT", degree="PhD Computer Science", field="CS")]
        )
        assert _education_score(profile) == 100.0

    def test_no_education(self):
        profile = ResumeProfile(education=[])
        assert _education_score(profile) == 30.0


# ── Format Score ──────────────────────────────────────────────────────────────


class TestFormatScore:
    def test_complete_profile(self, sample_profile):
        score = _format_score(sample_profile, "a" * 500)
        assert score >= 70.0

    def test_minimal_profile(self):
        profile = ResumeProfile()
        score = _format_score(profile, "short")
        assert score < 50.0


# ── Required Years Extraction ─────────────────────────────────────────────────


class TestExtractRequiredYears:
    def test_found(self):
        assert _extract_required_years("5+ years of experience required") == 5.0

    def test_range(self):
        years = _extract_required_years("3 to 7 years of experience")
        assert years == 5.0

    def test_default(self):
        assert _extract_required_years("No specific requirement") == 3.0


# ── Full ATS Score ────────────────────────────────────────────────────────────


class TestCalculateAtsScore:
    def test_returns_ats_report(self, sample_resume_text, sample_job_description, sample_profile):
        report = calculate_ats_score(sample_resume_text, sample_job_description, sample_profile)
        assert isinstance(report, ATSReport)
        assert 0 <= report.overall_score <= 100
        assert 0 <= report.keyword_score <= 100
        assert 0 <= report.skill_score <= 100
        assert 0 <= report.experience_score <= 100
        assert 0 <= report.education_score <= 100

    def test_has_recommendations(self, sample_resume_text, sample_job_description, sample_profile):
        report = calculate_ats_score(sample_resume_text, sample_job_description, sample_profile)
        assert len(report.recommendations) > 0

    def test_missing_keywords_identified(self, sample_resume_text, sample_job_description, sample_profile):
        report = calculate_ats_score(sample_resume_text, sample_job_description, sample_profile)
        assert isinstance(report.missing_keywords, list)
        assert isinstance(report.missing_skills, list)

    def test_perfect_match_high_score(self):
        text = "Python React Docker Kubernetes AWS PostgreSQL CI/CD agile microservices"
        job = "Python React Docker Kubernetes AWS PostgreSQL CI/CD agile microservices 5+ years experience"
        profile = ResumeProfile(
            skills=[
                Skill(name="python", category=SkillCategory.technical),
                Skill(name="react", category=SkillCategory.technical),
                Skill(name="docker", category=SkillCategory.technical),
                Skill(name="kubernetes", category=SkillCategory.technical),
                Skill(name="aws", category=SkillCategory.technical),
                Skill(name="postgresql", category=SkillCategory.technical),
            ],
            experience=[
                Experience(
                    title="Engineer",
                    company="Co",
                    start_date=date(2018, 1, 1),
                    end_date=date(2026, 1, 1),
                )
            ],
            education=[
                Education(institution="MIT", degree="Bachelor of Science", field="CS")
            ],
            years_experience=8.0,
            summary="Experienced engineer.",
            contact_info=ContactInfo(email="a@b.com", phone="123"),
        )
        report = calculate_ats_score(text, job, profile)
        assert report.overall_score >= 70.0

    def test_empty_inputs(self):
        profile = ResumeProfile()
        report = calculate_ats_score("", "", profile)
        assert report.overall_score >= 0

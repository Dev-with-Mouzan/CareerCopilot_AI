"""Tests for backend.services.job_normalizer — deterministic normalization from multiple sources."""

from __future__ import annotations

from datetime import datetime

import pytest

from backend.core.schemas import Job
from backend.services.job_normalizer import (
    _extract_skills_from_text,
    _normalize_employment_type,
    _normalize_location,
    _normalize_seniority,
    _parse_salary_range,
    normalize_generic_job,
    normalize_jobicy_job,
    normalize_linkedin_job,
    normalize_remotive_job,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def remotive_raw() -> dict:
    return {
        "id": 12345,
        "title": "Senior Python Developer",
        "company_name": "TechCorp",
        "candidate_required_location": "Remote",
        "description": "We need a Python developer with Django and PostgreSQL experience.",
        "salary": "$120,000 - $150,000",
        "tags": ["python", "django", "postgresql"],
        "job_type": "full-time",
        "publication_date": "2026-01-15T10:00:00Z",
        "url": "https://remotive.com/job/12345",
    }


@pytest.fixture
def jobicy_raw() -> dict:
    return {
        "id": 67890,
        "job_title": "Frontend Engineer",
        "company_name": "WebCo",
        "job_location": "Fully Remote",
        "job_description": "React and TypeScript developer needed.",
        "annual_salary_min": 90000,
        "annual_salary_max": 130000,
        "job_type": "remote",
        "pubDate": "2026-02-01 12:00:00",
        "url": "https://jobicy.com/job/67890",
    }


@pytest.fixture
def linkedin_raw() -> dict:
    return {
        "jobId": "ln-001",
        "title": "Machine Learning Engineer",
        "companyName": "AI Labs",
        "location": "San Francisco, CA",
        "description": "PyTorch and TensorFlow experience required.",
        "salaryMin": 140000,
        "salaryMax": 180000,
        "currency": "USD",
        "employmentType": "full-time",
        "seniorityLevel": "senior",
        "postedDate": "2026-03-10T08:00:00Z",
        "url": "https://linkedin.com/jobs/ln-001",
    }


@pytest.fixture
def generic_raw() -> dict:
    return {
        "title": "DevOps Engineer",
        "company": "CloudInc",
        "location": "Remote",
        "description": "Kubernetes, Terraform, and AWS required.",
        "url": "https://example.com/job/devops-1",
        "salary": "$100,000 - $130,000",
        "job_type": "contract",
        "seniority": "mid",
        "posted_at": "2026-04-01",
    }


# ── Salary Parsing ────────────────────────────────────────────────────────────


class TestParseSalaryRange:
    def test_range(self):
        lo, hi, cur = _parse_salary_range("$120,000 - $150,000")
        assert lo == 120000
        assert hi == 150000
        assert cur == "USD"

    def test_range_with_k(self):
        lo, hi, _ = _parse_salary_range("$80K - $120K")
        assert lo == 80000
        assert hi == 120000

    def test_single_value(self):
        lo, hi, _ = _parse_salary_range("$100,000")
        assert lo == 100000
        assert hi == 100000

    def test_empty(self):
        lo, hi, cur = _parse_salary_range("")
        assert lo is None
        assert hi is None

    def test_no_salary(self):
        lo, hi, _ = _parse_salary_range("Competitive compensation")
        assert lo is None


# ── Location Normalization ────────────────────────────────────────────────────


class TestNormalizeLocation:
    def test_remote(self):
        loc, is_remote = _normalize_location("Fully Remote")
        assert loc == "Remote"
        assert is_remote is True

    def test_100_percent_remote(self):
        loc, is_remote = _normalize_location("100% Remote")
        assert is_remote is True

    def test_city(self):
        loc, is_remote = _normalize_location("San Francisco, CA")
        assert loc == "San Francisco, CA"
        assert is_remote is False

    def test_empty(self):
        loc, is_remote = _normalize_location("")
        assert loc == ""


# ── Employment Type ───────────────────────────────────────────────────────────


class TestNormalizeEmploymentType:
    def test_fulltime(self):
        assert _normalize_employment_type("full-time") == "full-time"
        assert _normalize_employment_type("Fulltime") == "full-time"

    def test_contract(self):
        assert _normalize_employment_type("contract") == "contract"
        assert _normalize_employment_type("freelance") == "contract"

    def test_internship(self):
        assert _normalize_employment_type("internship") == "internship"

    def test_default(self):
        assert _normalize_employment_type("something else") == "full-time"


# ── Seniority ─────────────────────────────────────────────────────────────────


class TestNormalizeSeniority:
    def test_senior(self):
        assert _normalize_seniority("Senior Engineer") == "senior"

    def test_junior(self):
        assert _normalize_seniority("Junior Developer", "") == "junior"

    def test_lead(self):
        assert _normalize_seniority("Staff Engineer") == "lead"

    def test_default_mid(self):
        assert _normalize_seniority("Software Engineer") == "mid"


# ── Skill Extraction from Description ─────────────────────────────────────────


class TestExtractSkillsFromText:
    def test_finds_skills(self):
        skills = _extract_skills_from_text("Python, Django, and PostgreSQL required.")
        assert "python" in skills
        assert "django" in skills
        assert "postgresql" in skills

    def test_empty(self):
        assert _extract_skills_from_text("") == []

    def test_no_skills(self):
        assert _extract_skills_from_text("Hello world") == []


# ── Source Normalizers ────────────────────────────────────────────────────────


class TestNormalizeRemotiveJob:
    def test_basic(self, remotive_raw):
        job = normalize_remotive_job(remotive_raw)
        assert isinstance(job, Job)
        assert job.title == "Senior Python Developer"
        assert job.company == "TechCorp"
        assert job.remote is True
        assert job.source == "remotive"
        assert job.salary_min == 120000
        assert job.salary_max == 150000

    def test_skills_from_tags(self, remotive_raw):
        job = normalize_remotive_job(remotive_raw)
        assert "python" in job.skills

    def test_posted_at_parsed(self, remotive_raw):
        job = normalize_remotive_job(remotive_raw)
        assert job.posted_at is not None


class TestNormalizeJobicyJob:
    def test_basic(self, jobicy_raw):
        job = normalize_jobicy_job(jobicy_raw)
        assert job.title == "Frontend Engineer"
        assert job.company == "WebCo"
        assert job.remote is True
        assert job.source == "jobicy"
        assert job.salary_min == 90000

    def test_skills_from_description(self, jobicy_raw):
        job = normalize_jobicy_job(jobicy_raw)
        assert "react" in job.skills or "typescript" in job.skills


class TestNormalizeLinkedinJob:
    def test_basic(self, linkedin_raw):
        job = normalize_linkedin_job(linkedin_raw)
        assert job.title == "Machine Learning Engineer"
        assert job.company == "AI Labs"
        assert job.source == "linkedin"
        assert job.seniority == "senior"

    def test_salary(self, linkedin_raw):
        job = normalize_linkedin_job(linkedin_raw)
        assert job.salary_min == 140000
        assert job.salary_max == 180000


class TestNormalizeGenericJob:
    def test_basic(self, generic_raw):
        job = normalize_generic_job(generic_raw)
        assert job.title == "DevOps Engineer"
        assert job.company == "CloudInc"
        assert job.remote is True
        assert job.employment_type == "contract"
        assert job.seniority == "mid"

    def test_skills_extracted(self, generic_raw):
        job = normalize_generic_job(generic_raw)
        assert "kubernetes" in job.skills or "terraform" in job.skills

    def test_flexible_field_names(self):
        job = normalize_generic_job({
            "position": "Data Analyst",
            "employer": "DataCo",
            "city": "New York",
            "details": "SQL and pandas required.",
            "apply_url": "https://example.com/apply",
        })
        assert job.title == "Data Analyst"
        assert job.company == "DataCo"

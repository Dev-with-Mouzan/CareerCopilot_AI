"""Tests for backend.services.resume_parser — deterministic parsing of text resumes."""

from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path

import pytest

from backend.core.schemas import SkillCategory
from backend.services.resume_parser import (
    _clean_text,
    _extract_contact,
    _extract_skills,
    _normalize_skill,
    _parse_date,
    _parse_education,
    _parse_experiences,
    _split_sections,
    compute_file_hash,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_RESUME = textwrap.dedent("""\
    John Doe
    john@example.com | +1 555 123 4567 | linkedin.com/in/johndoe | github.com/johndoe

    Professional Summary
    Senior software engineer with 8+ years of experience in Python and JavaScript.

    Experience
    Senior Software Engineer at Acme Corp
    Jan 2020 - Present
    Built microservices with Python and FastAPI. Deployed on AWS using Docker and Kubernetes.

    Frontend Developer at StartupXYZ
    Mar 2017 - Dec 2019
    Developed React applications with TypeScript. Used Redux for state management.

    Education
    Bachelor of Science in Computer Science
    MIT
    Sep 2013 - Jun 2017
    GPA: 3.8

    Skills
    Python, JavaScript, TypeScript, React, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Git

    Projects
    Open Source Dashboard
    A real-time analytics dashboard built with React, D3.js, and Python backend.

    Certifications
    AWS Solutions Architect
""")

EMPTY_RESUME = "Just some random text without sections."


@pytest.fixture
def sample_resume_text() -> str:
    return SAMPLE_RESUME


@pytest.fixture
def sample_resume_path(tmp_path: Path) -> Path:
    p = tmp_path / "resume.txt"
    p.write_text(SAMPLE_RESUME, encoding="utf-8")
    return p


# ── Text Cleaning ─────────────────────────────────────────────────────────────


class TestCleanText:
    def test_removes_excessive_whitespace(self):
        result = _clean_text("hello    world\t\t\n\n\n\n\nfoo")
        assert "hello world" in result
        assert "\n\n\n" not in result

    def test_strips_unicode(self):
        result = _clean_text("caf\u00e9\u200bresume")
        assert "\u200b" not in result


# ── Skill Normalization ───────────────────────────────────────────────────────


class TestNormalizeSkill:
    def test_known_alias(self):
        assert _normalize_skill("ReactJS") == "reactjs"
        assert _normalize_skill("  Python  ") == "python"

    def test_lowercased(self):
        assert _normalize_skill("JavaScript") == "javascript"

    def test_strips_special_chars(self):
        result = _normalize_skill("C++!")
        assert "!" not in result


# ── Contact Extraction ────────────────────────────────────────────────────────


class TestExtractContact:
    def test_extracts_email(self):
        contact = _extract_contact("Contact: john@example.com")
        assert contact.email == "john@example.com"

    def test_extracts_phone(self):
        contact = _extract_contact("Call me at +1 555 123 4567")
        assert "555" in contact.phone

    def test_extracts_linkedin(self):
        contact = _extract_contact("linkedin.com/in/johndoe")
        assert "linkedin.com" in contact.linkedin

    def test_extracts_github(self):
        contact = _extract_contact("github.com/johndoe")
        assert "github.com" in contact.github

    def test_empty_text(self):
        contact = _extract_contact("")
        assert contact.email == ""


# ── Skill Extraction ──────────────────────────────────────────────────────────


class TestExtractSkills:
    def test_finds_known_skills(self, sample_resume_text):
        skills = _extract_skills(sample_resume_text)
        skill_names = {s.name for s in skills}
        assert "python" in skill_names
        assert "react" in skill_names
        assert "docker" in skill_names
        assert "kubernetes" in skill_names

    def test_no_skills_in_empty_text(self):
        skills = _extract_skills("hello world no skills here")
        assert len(skills) == 0

    def test_skills_have_category(self, sample_resume_text):
        skills = _extract_skills(sample_resume_text)
        for s in skills:
            assert isinstance(s.category, SkillCategory)

    def test_soft_skills_detected(self):
        text = "I have strong leadership and communication skills."
        skills = _extract_skills(text)
        names = {s.name for s in skills}
        assert "leadership" in names or "communication" in names


# ── Section Detection ─────────────────────────────────────────────────────────


class TestSplitSections:
    def test_finds_sections(self, sample_resume_text):
        sections = _split_sections(sample_resume_text)
        assert "summary" in sections or "experience" in sections

    def test_experience_section_content(self, sample_resume_text):
        sections = _split_sections(sample_resume_text)
        if "experience" in sections:
            assert "Acme Corp" in sections["experience"]

    def test_empty_text(self):
        sections = _split_sections("")
        assert len(sections) == 0


# ── Date Parsing ──────────────────────────────────────────────────────────────


class TestParseDate:
    def test_valid_date(self):
        d = _parse_date("Jan", "2020")
        assert d == date(2020, 1, 1)

    def test_invalid_month(self):
        assert _parse_date("Xyz", "2020") is None

    def test_invalid_year(self):
        assert _parse_date("Jan", "abcd") is None


# ── Experience Parsing ────────────────────────────────────────────────────────


class TestParseExperiences:
    def test_parses_experience(self, sample_resume_text):
        sections = _split_sections(sample_resume_text)
        exp_text = sections.get("experience", "")
        exps = _parse_experiences(exp_text)
        assert len(exps) >= 1
        titles = [e.title for e in exps]
        assert any("Engineer" in t or "Developer" in t for t in titles)

    def test_empty_text(self):
        assert _parse_experiences("") == []


# ── Education Parsing ─────────────────────────────────────────────────────────


class TestParseEducation:
    def test_parses_degree(self, sample_resume_text):
        sections = _split_sections(sample_resume_text)
        edu_text = sections.get("education", "")
        entries = _parse_education(edu_text)
        assert len(entries) >= 1
        assert any("Bachelor" in e.degree or "Computer Science" in e.degree for e in entries)

    def test_gpa_extracted(self, sample_resume_text):
        sections = _split_sections(sample_resume_text)
        edu_text = sections.get("education", "")
        entries = _parse_education(edu_text)
        gpas = [e.gpa for e in entries if e.gpa is not None]
        assert any(g and g > 3.0 for g in gpas)


# ── File Hash ─────────────────────────────────────────────────────────────────


class TestComputeFileHash:
    def test_same_content_same_hash(self, tmp_path):
        p1 = tmp_path / "a.txt"
        p2 = tmp_path / "b.txt"
        p1.write_text("hello")
        p2.write_text("hello")
        assert compute_file_hash(p1) == compute_file_hash(p2)

    def test_different_content_different_hash(self, tmp_path):
        p1 = tmp_path / "a.txt"
        p2 = tmp_path / "b.txt"
        p1.write_text("hello")
        p2.write_text("world")
        assert compute_file_hash(p1) != compute_file_hash(p2)

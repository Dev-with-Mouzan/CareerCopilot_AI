"""Tests for backend.services.job_deduplicator — deterministic deduplication."""

from __future__ import annotations

import pytest

from backend.core.schemas import Job
from backend.services.job_deduplicator import _fingerprint, _normalize, _normalize_url, deduplicate, find_duplicates


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_job(
    title: str,
    company: str,
    location: str = "Remote",
    source_url: str = "",
    description: str = "",
    skills: list[str] | None = None,
    **kwargs,
) -> Job:
    return Job(
        title=title,
        company=company,
        location=location,
        source_url=source_url,
        description=description,
        skills=skills or [],
        **kwargs,
    )


# ── Fingerprinting ────────────────────────────────────────────────────────────


class TestFingerprint:
    def test_deterministic(self):
        job = _make_job("Engineer", "Acme", "Remote")
        fp1 = _fingerprint(job)
        fp2 = _fingerprint(job)
        assert fp1 == fp2

    def test_different_titles(self):
        fp1 = _fingerprint(_make_job("Engineer", "Acme"))
        fp2 = _fingerprint(_make_job("Developer", "Acme"))
        assert fp1 != fp2

    def test_different_companies(self):
        fp1 = _fingerprint(_make_job("Engineer", "Acme"))
        fp2 = _fingerprint(_make_job("Engineer", "Beta"))
        assert fp1 != fp2

    def test_same_different_case(self):
        fp1 = _fingerprint(_make_job("Engineer", "ACME"))
        fp2 = _fingerprint(_make_job("engineer", "acme"))
        assert fp1 == fp2


# ── URL Normalization ─────────────────────────────────────────────────────────


class TestNormalizeUrl:
    def test_strips_query(self):
        assert _normalize_url("https://example.com/job?ref=abc") == "example.com/job"

    def test_strips_fragment(self):
        assert _normalize_url("https://example.com/job#section") == "example.com/job"

    def test_strips_protocol(self):
        assert _normalize_url("http://example.com") == "example.com"

    def test_empty(self):
        assert _normalize_url("") == ""


# ── Normalize ─────────────────────────────────────────────────────────────────


class TestNormalize:
    def test_unicode(self):
        result = _normalize("R\u00e9sum\u00e9")
        assert "e" in result

    def test_lowercased(self):
        assert _normalize("HELLO WORLD") == "hello world"


# ── Deduplication ─────────────────────────────────────────────────────────────


class TestDeduplicate:
    def test_removes_exact_duplicates(self):
        jobs = [
            _make_job("Engineer", "Acme", "Remote", description="Build things"),
            _make_job("Engineer", "Acme", "Remote", description="Build things"),
        ]
        result = deduplicate(jobs)
        assert len(result) == 1

    def test_keeps_distinct_jobs(self):
        jobs = [
            _make_job("Engineer", "Acme", "Remote"),
            _make_job("Developer", "Beta", "Remote"),
            _make_job("Analyst", "Gamma", "New York"),
        ]
        result = deduplicate(jobs)
        assert len(result) == 3

    def test_merges_skills_on_duplicate(self):
        jobs = [
            _make_job("Engineer", "Acme", skills=["python"]),
            _make_job("Engineer", "Acme", skills=["react"]),
        ]
        result = deduplicate(jobs)
        assert len(result) == 1
        assert set(result[0].skills) == {"python", "react"}

    def test_url_dedup(self):
        jobs = [
            _make_job("Engineer A", "Acme", source_url="https://example.com/job/1"),
            _make_job("Engineer B", "Acme", source_url="https://example.com/job/1?ref=src"),
        ]
        result = deduplicate(jobs)
        assert len(result) == 1

    def test_empty_list(self):
        assert deduplicate([]) == []

    def test_single_job(self):
        jobs = [_make_job("Engineer", "Acme")]
        assert len(deduplicate(jobs)) == 1

    def test_near_duplicate_by_content(self):
        desc = "We need a Python developer with Django and REST API experience. Must have 5 years."
        jobs = [
            _make_job("Python Dev", "Acme", description=desc),
            _make_job("Python Dev", "Acme", description=desc + " Additional detail."),
        ]
        result = deduplicate(jobs, similarity_threshold=0.7)
        assert len(result) == 1

    def test_preserves_first_source(self):
        jobs = [
            _make_job("Engineer", "Acme", source="linkedin"),
            _make_job("Engineer", "Acme", source="remotive"),
        ]
        result = deduplicate(jobs)
        assert result[0].source == "linkedin"


# ── Find Duplicates ───────────────────────────────────────────────────────────


class TestFindDuplicates:
    def test_finds_exact_dupes(self):
        jobs = [
            _make_job("Engineer", "Acme"),
            _make_job("Engineer", "Acme"),
            _make_job("Developer", "Beta"),
        ]
        pairs = find_duplicates(jobs)
        assert len(pairs) >= 1
        assert (0, 1) in pairs

    def test_no_duplicates(self):
        jobs = [
            _make_job("Engineer", "Acme"),
            _make_job("Developer", "Beta"),
        ]
        pairs = find_duplicates(jobs)
        assert pairs == []

    def test_empty_list(self):
        assert find_duplicates([]) == []

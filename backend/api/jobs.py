"""Job endpoints — manual search + resume-based matching via job_graph pipeline."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from backend.core.schemas import UserProfile
from backend.core.store import (
    _job_matches,
    get_resume,
    list_generic,
    list_resumes,
    store_generic,
    get_generic,
)
from backend.graphs.orchestrator import run_job_pipeline
from backend.security.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs")


class _SearchBody(BaseModel):
    target_role: str | None = None
    keywords: str | None = None
    location: str | None = None
    resume_id: str | None = None


@router.post("/search")
async def search_jobs(
    body: _SearchBody,
    user: UserProfile = Depends(get_current_user),
):
    """Search jobs either manually (keywords/location) or based on a resume."""
    target = (body.target_role or body.keywords or "").strip()
    resume_id = uuid.UUID(body.resume_id) if body.resume_id else None

    # Load resume profile if resume_id provided for matching
    resume_profile = None
    if resume_id:
        resume = get_resume(resume_id)
        if resume is not None:
            resume_profile = resume.parsed_profile

    # Derive search keywords from the resume when no explicit target given
    if not target and resume_profile:
        skills = [
            s.get("name", "")
            for s in resume_profile.get("skills", [])
            if isinstance(s, dict) and s.get("name")
        ][:12]
        target_roles = resume_profile.get("target_roles", []) or []
        if target_roles:
            target = target_roles[0]
        elif resume_profile.get("experience"):
            latest = resume_profile["experience"][0]
            if isinstance(latest, dict):
                target = latest.get("title", "")
        if skills:
            target = (target + " " + " ".join(skills[:6])).strip()

    if not target:
        target = "software engineer"

    result = await run_job_pipeline(
        user_id=user.id,
        resume_id=resume_id or uuid.UUID("00000000-0000-0000-0000-000000000000"),
        target_role=target,
        resume_profile=resume_profile or {},
    )

    matched = result.get("matched_jobs", [])
    pipeline_id = str(uuid.uuid4())
    store_generic(_job_matches, uuid.UUID(pipeline_id), {
        "user_id": user.id,
        "target_role": target,
        "jobs": matched,
        "recommendations": result.get("recommendations", []),
    })

    return {
        "pipeline_id": pipeline_id,
        "status": "completed",
        "jobs": matched,
        "recommendations": result.get("recommendations", []),
    }


@router.get("/status/{pipeline_id}")
async def job_status(pipeline_id: str):
    data = get_generic(_job_matches, uuid.UUID(pipeline_id)) if _is_valid_uuid(pipeline_id) else None
    if data is None:
        return {"pipeline_id": pipeline_id, "status": "pending", "jobs": []}
    return {"pipeline_id": pipeline_id, "status": "completed", "jobs": data.get("jobs", [])}


@router.get("")
async def list_jobs(user: UserProfile = Depends(get_current_user)):
    all_matches = list_generic(_job_matches, user.id)
    jobs = []
    for m in all_matches:
        jobs.extend(m.get("jobs", []))
    return {"jobs": jobs, "total": len(jobs)}


@router.get("/{job_id}")
async def get_job(job_id: uuid.UUID):
    return {"error": "Job not found"}, 404


@router.post("/{job_id}/analyze")
async def analyze_job(job_id: uuid.UUID, user: UserProfile = Depends(get_current_user)):
    """Run ATS analysis of the user's resume against a single matched job."""
    from backend.graphs.ats_graph import ats_pipeline

    # Find the job across stored pipelines for this user
    target_job = None
    for match in list_generic(_job_matches, user.id):
        for job in match.get("jobs", []):
            jid = job.get("id") or job.get("job_id") or job.get("source_job_id")
            if jid is not None and str(jid) == str(job_id):
                target_job = job
                break
        if target_job:
            break

    if target_job is None:
        return {"error": "Job not found"}, 404

    resume = None
    resumes = list_resumes(user.id)
    resume = resumes[0] if resumes else None
    if resume is None:
        return {"error": "Upload a resume first to run ATS analysis"}, 400

    job_desc = target_job.get("description") or ""
    if not job_desc:
        return {"error": "This job has no description to analyze against"}, 400

    state = {
        "user_id": user.id,
        "resume_id": resume.id,
        "job_id": job_id,
        "resume_text": resume.raw_text,
        "job_description": job_desc,
    }
    result = await ats_pipeline.ainvoke(state)
    report = result.get("report", {}) or {}

    # Merge into the job's existing match for display
    if "match" not in target_job:
        target_job["match"] = {}
    target_job["match"]["overall_score"] = report.get("overall_score", 0) / 100
    target_job["match"]["missing_skills"] = report.get("missing_skills", [])
    target_job["match"]["missing_keywords"] = report.get("missing_keywords", [])
    target_job["match"]["ats_report"] = report

    return {
        "job_id": str(job_id),
        "report": report,
        "recommendations": report.get("recommendations", []),
    }


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

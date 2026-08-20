"""Job search and matching endpoints."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Job, JobMatch
from backend.core.schemas import UserProfile
from backend.db.session import get_db
from backend.security.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs")


# ── Background pipeline jobs (backward-compatible with old /api/run-crew) ────
import time

_MAX_PIPELINE_JOBS = 200  # prevent unbounded memory growth
_pipeline_jobs: dict[str, dict] = {}


def _cleanup_old_pipelines() -> None:
    """Remove completed/failed pipelines older than 1 hour."""
    now = time.time()
    stale = [
        pid for pid, job in _pipeline_jobs.items()
        if job.get("status") in ("done", "failed")
        and now - job.get("created_at_ts", now) > 3600
    ]
    for pid in stale:
        del _pipeline_jobs[pid]


def _register_pipeline(pipeline_id: str, job: dict) -> None:
    """Register a pipeline job, evicting old ones if at capacity."""
    _cleanup_old_pipelines()
    if len(_pipeline_jobs) >= _MAX_PIPELINE_JOBS:
        # Evict oldest completed job
        for pid, j in list(_pipeline_jobs.items()):
            if j.get("status") in ("done", "failed"):
                del _pipeline_jobs[pid]
                break
    _pipeline_jobs[pipeline_id] = job


# ── Search & match ───────────────────────────────────────────────────────────


class JobSearchRequest(BaseModel):
    target_role: str = "Software Engineer"
    keywords: str = ""


@router.post("/search", status_code=status.HTTP_201_CREATED)
async def search_jobs(
    body: JobSearchRequest,
    background_tasks: BackgroundTasks,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger the job search + matching graph.  Returns a pollable pipeline ID."""
    import uuid

    pipeline_id = str(uuid.uuid4())
    _register_pipeline(pipeline_id, {
        "status": "running",
        "result": None,
        "error": None,
        "user_id": str(user.id),
        "created_at_ts": time.time(),
    })

    background_tasks.add_task(
        _run_job_graph, pipeline_id, str(user.id), body.target_role, body.keywords.split(",")
    )

    return {
        "pipeline_id": pipeline_id,
        "status": "running",
        "message": "Job search started. Poll GET /api/status/{pipeline_id} for results.",
    }


async def _run_job_graph(pipeline_id: str, user_id: str, target_role: str, keywords: list[str]) -> None:
    try:
        from backend.graphs.job_graph import job_pipeline

        result = await job_pipeline.ainvoke(
            {
                "user_id": UUID(user_id),
                "target_role": target_role,
                "query_keywords": keywords,
            }
        )
        _pipeline_jobs[pipeline_id]["status"] = "done"
        _pipeline_jobs[pipeline_id]["result"] = result.get("matched_jobs", [])
    except Exception as exc:
        _pipeline_jobs[pipeline_id]["status"] = "failed"
        _pipeline_jobs[pipeline_id]["error"] = str(exc)
        logger.exception("Job graph failed for pipeline %s", pipeline_id)


# ── Backward-compatible status endpoint ──────────────────────────────────────


@router.get("/status/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str):
    if pipeline_id not in _pipeline_jobs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    job = _pipeline_jobs[pipeline_id]
    return {
        "job_id": pipeline_id,
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error"),
    }


# ── List matched jobs ────────────────────────────────────────────────────────


@router.get("")
async def list_jobs(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(JobMatch, Job)
        .join(Job, JobMatch.job_id == Job.id)
        .where(JobMatch.user_id == user.id)
        .order_by(JobMatch.overall_score.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()
    return {
        "jobs": [
            {
                "job_id": str(match.job_id),
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "remote": job.remote,
                "overall_score": match.overall_score,
                "skill_score": match.skill_score,
                "missing_skills": match.missing_skills,
                "source_url": job.source_url,
            }
            for match, job in rows
        ],
        "offset": offset,
        "limit": limit,
    }


# ── Get job details ──────────────────────────────────────────────────────────


@router.get("/{job_id}")
async def get_job(
    job_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    match_result = await db.execute(
        select(JobMatch).where(JobMatch.job_id == job_id, JobMatch.user_id == user.id)
    )
    match = match_result.scalar_one_or_none()

    return {
        "id": str(job.id),
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "remote": job.remote,
        "description": job.description,
        "skills": job.skills,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "employment_type": job.employment_type,
        "seniority": job.seniority,
        "source_url": job.source_url,
        "match": {
            "overall_score": match.overall_score,
            "skill_score": match.skill_score,
            "experience_score": match.experience_score,
            "reasoning": match.reasoning,
            "missing_skills": match.missing_skills,
        }
        if match
        else None,
    }


# ── Analyze specific job match ──────────────────────────────────────────────


@router.post("/{job_id}/analyze")
async def analyze_job_match(
    job_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run ATS analysis for the user's resume against this job."""
    from backend.graphs.ats_graph import ats_pipeline

    result = await ats_pipeline.ainvoke(
        {
            "user_id": user.id,
            "job_id": job_id,
        }
    )
    return result.get("report", {})

"""ATS analysis and optimisation endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import ATSReport as ATSReportModel, Resume, Job
from backend.core.schemas import UserProfile
from backend.db.session import get_db
from backend.security.auth import get_current_user
from backend.services.llm_service import TaskCategory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ats")


# ── Run ATS analysis ─────────────────────────────────────────────────────────


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
async def analyze_ats(
    resume_id: UUID,
    job_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run ATS analysis for a resume against a job description."""
    from backend.graphs.ats_graph import ats_pipeline

    report = await ats_pipeline.ainvoke(
        {
            "user_id": user.id,
            "resume_id": resume_id,
            "job_id": job_id,
        }
    )
    return report.get("report", {})


# ── List ATS reports ─────────────────────────────────────────────────────────


@router.get("/reports")
async def list_reports(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ATSReportModel)
        .where(ATSReportModel.user_id == user.id)
        .order_by(ATSReportModel.created_at.desc())
    )
    rows = result.scalars().all()
    return {
        "reports": [
            {
                "id": str(r.id),
                "overall_score": r.overall_score,
                "keyword_score": r.keyword_score,
                "skill_score": r.skill_score,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


# ── Get specific report ──────────────────────────────────────────────────────


@router.get("/reports/{report_id}")
async def get_report(
    report_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ATSReportModel).where(
            ATSReportModel.id == report_id,
            ATSReportModel.user_id == user.id,
        )
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return {
        "id": str(report.id),
        "overall_score": report.overall_score,
        "keyword_score": report.keyword_score,
        "skill_score": report.skill_score,
        "experience_score": report.experience_score,
        "semantic_score": report.semantic_score,
        "education_score": report.education_score,
        "report_data": report.report_data,
        "created_at": report.created_at.isoformat(),
    }


# ── Optimisation suggestions ─────────────────────────────────────────────────


@router.post("/optimize")
async def optimize_resume(
    resume_id: UUID,
    job_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return resume optimisation suggestions for a given job."""
    resume_result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = resume_result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    from backend.services.llm_service import ModelRouter, TaskCategory

    llm = ModelRouter()
    prompt = (
        f"Given the resume below and the job description, provide specific optimisation "
        f"suggestions (bullet points) to improve ATS compatibility.\n\n"
        f"RESUME:\n{(resume.raw_text or '')[:4000]}\n\n"
        f"JOB DESCRIPTION:\n{(job.description or '')[:4000]}"
    )
    response = await llm.complete(
        messages=[{"role": "user", "content": prompt}],
        category=TaskCategory.ATS_EXPLANATION,
    )
    return {"suggestions": response}

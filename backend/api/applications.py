"""Application tracking endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Application as ApplicationModel, Job, ResumeVersion
from backend.core.schemas import ApplicationStatus, UserProfile
from backend.db.session import get_db
from backend.security.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications")


# ── Create application ───────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_application(
    job_id: UUID,
    resume_version_id: UUID,
    notes: str = "",
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(ApplicationModel).where(
            ApplicationModel.user_id == user.id,
            ApplicationModel.job_id == job_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application already exists for this job.")

    application = ApplicationModel(
        user_id=user.id,
        job_id=job_id,
        resume_version_id=resume_version_id,
        status=ApplicationStatus.saved.value,
        notes=notes,
    )
    db.add(application)
    await db.commit()

    return {
        "id": str(application.id),
        "status": application.status,
        "created_at": application.created_at.isoformat(),
    }


# ── List applications ────────────────────────────────────────────────────────


@router.get("")
async def list_applications(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    app_status: str | None = Query(None, alias="status"),
):
    query = (
        select(ApplicationModel, Job)
        .join(Job, ApplicationModel.job_id == Job.id)
        .where(ApplicationModel.user_id == user.id)
        .order_by(ApplicationModel.updated_at.desc())
    )
    if app_status:
        query = query.where(ApplicationModel.status == app_status)

    result = await db.execute(query.offset(offset).limit(limit))
    rows = result.all()
    return {
        "applications": [
            {
                "id": str(app.id),
                "job_id": str(app.job_id),
                "title": job.title,
                "company": job.company,
                "status": app.status,
                "ats_score": app.ats_score,
                "match_score": app.match_score,
                "notes": app.notes,
                "created_at": app.created_at.isoformat(),
                "updated_at": app.updated_at.isoformat(),
            }
            for app, job in rows
        ],
        "offset": offset,
        "limit": limit,
    }


# ── Update application status ────────────────────────────────────────────────


@router.patch("/{application_id}")
async def update_application(
    application_id: UUID,
    app_status: str | None = None,
    notes: str | None = None,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApplicationModel).where(
            ApplicationModel.id == application_id,
            ApplicationModel.user_id == user.id,
        )
    )
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if app_status:
        # Validate status value
        valid = {s.value for s in ApplicationStatus}
        if app_status not in valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status. Must be one of: {valid}")
        application.status = app_status
    if notes is not None:
        application.notes = notes

    await db.commit()
    return {"id": str(application.id), "status": application.status, "notes": application.notes}


# ── Analytics ────────────────────────────────────────────────────────────────


@router.get("/analytics")
async def get_analytics(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApplicationModel.status, func.count())
        .where(ApplicationModel.user_id == user.id)
        .group_by(ApplicationModel.status)
    )
    status_counts = {row[0]: row[1] for row in result.all()}

    total = sum(status_counts.values())
    avg_ats = await db.execute(
        select(func.avg(ApplicationModel.ats_score)).where(
            ApplicationModel.user_id == user.id,
            ApplicationModel.ats_score.isnot(None),
        )
    )
    avg_match = await db.execute(
        select(func.avg(ApplicationModel.match_score)).where(
            ApplicationModel.user_id == user.id,
            ApplicationModel.match_score.isnot(None),
        )
    )

    return {
        "total_applications": total,
        "status_breakdown": status_counts,
        "avg_ats_score": round(avg_ats.scalar() or 0, 2),
        "avg_match_score": round(avg_match.scalar() or 0, 2),
    }

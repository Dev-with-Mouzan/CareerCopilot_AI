"""Resume management endpoints."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.models import Resume, ResumeVersion, User
from backend.core.schemas import ResumeProfile, ResumeVersion as ResumeVersionSchema, UserProfile
from backend.db.session import get_db
from backend.security.auth import get_current_user
from backend.security.sanitization import sanitize_file_upload

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/resumes")


# Upload & parse 


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File()],
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a resume file (PDF/DOCX/TXT).  Parsing runs in background."""
    raw = await sanitize_file_upload(file)

    # Ensure user exists in DB
    existing = await db.execute(select(User).where(User.id == user.id))
    if existing.scalar_one_or_none() is None:
        db.add(User(id=user.id, email=user.email, name=user.name))
        await db.flush()

    # Decode bytes, strip null bytes and control chars (keeps newlines/tabs)
    _text = raw.decode("utf-8", errors="replace")[:100_000]
    _text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", _text)

    resume = Resume(
        user_id=user.id,
        original_filename=file.filename,
        raw_text=_text,
        parsing_status="pending",
    )
    db.add(resume)
    await db.flush()

    # Create initial version
    content_hash = hashlib.sha256(resume.raw_text.encode()).hexdigest()
    version = ResumeVersion(
        resume_id=resume.id,
        version_number=1,
        content_hash=content_hash,
        content=resume.raw_text,
    )
    db.add(version)
    await db.commit()

    # Schedule background parsing
    background_tasks.add_task(_parse_resume, str(resume.id), str(version.id))

    return {
        "resume_id": str(resume.id),
        "version_id": str(version.id),
        "status": "parsing",
        "filename": file.filename,
    }


async def _parse_resume(resume_id: str, version_id: str) -> None:
    """Background task: invoke the resume parser graph."""
    try:
        from backend.graphs.resume_graph import resume_pipeline

        await resume_pipeline.ainvoke(
            {
                "resume_id": UUID(resume_id),
                "resume_version_id": UUID(version_id),
                "user_id": None,
                "resume_text": "",
                "resume_profile": {},
                "parsing_status": "pending",
                "error": None,
            }
        )
    except Exception:
        logger.exception("Resume parsing failed for %s", resume_id)


# ── List user resumes ────────────────────────────────────────────────────────


@router.get("")
async def list_resumes(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())
    )
    rows = result.scalars().all()
    return {
        "resumes": [
            {
                "id": str(r.id),
                "filename": r.original_filename,
                "status": r.parsing_status,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }


# ── Get resume details ──────────────────────────────────────────────────────


@router.get("/{resume_id}")
async def get_resume(
    resume_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_user_resume(db, user.id, resume_id)
    versions = await db.execute(
        select(ResumeVersion).where(ResumeVersion.resume_id == resume_id).order_by(ResumeVersion.version_number)
    )
    ver_rows = versions.scalars().all()
    return {
        "id": str(resume.id),
        "filename": resume.original_filename,
        "status": resume.parsing_status,
        "parsed_profile": resume.parsed_profile,
        "versions": [
            {
                "id": str(v.id),
                "version_number": v.version_number,
                "target_role": v.target_role,
                "ats_score": v.ats_score,
                "created_at": v.created_at.isoformat(),
            }
            for v in ver_rows
        ],
    }


# ── Delete resume ────────────────────────────────────────────────────────────


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_user_resume(db, user.id, resume_id)
    await db.delete(resume)
    await db.commit()


# ── Create new version ──────────────────────────────────────────────────────


@router.post("/{resume_id}/versions", status_code=status.HTTP_201_CREATED)
async def create_version(
    resume_id: UUID,
    target_role: str = "",
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_user_resume(db, user.id, resume_id)

    count = await db.execute(
        select(func.count()).select_from(ResumeVersion).where(ResumeVersion.resume_id == resume_id)
    )
    next_num = count.scalar() + 1

    content_hash = hashlib.sha256((resume.raw_text or "").encode()).hexdigest()
    version = ResumeVersion(
        resume_id=resume_id,
        version_number=next_num,
        target_role=target_role,
        content_hash=content_hash,
        content=resume.raw_text,
    )
    db.add(version)
    await db.commit()

    return {
        "version_id": str(version.id),
        "version_number": next_num,
    }


# ── Helper ───────────────────────────────────────────────────────────────────


async def _get_user_resume(db: AsyncSession, user_id: UUID, resume_id: UUID) -> Resume:
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
    )
    resume = result.scalar_one_or_none()
    if resume is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume

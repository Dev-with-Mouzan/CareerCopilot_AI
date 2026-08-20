"""Cover letter generation endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import CoverLetter as CoverLetterModel
from backend.core.schemas import CoverLetterRequest, UserProfile
from backend.db.session import get_db
from backend.security.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cover-letters")


# ── Generate cover letter ────────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
async def generate_cover_letter(
    request: CoverLetterRequest,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a tailored cover letter for a specific job application."""
    from backend.graphs.cover_letter_graph import cover_letter_pipeline

    initial_state = {
        "user_id": user.id,
        "resume_id": request.resume_id,
        "job_id": request.job_id,
        "resume_text": "",
        "job_description": request.job_description,
        "job_title": request.job_title,
        "company_name": request.company_name,
        "resume_profile": {},
        "tone": request.tone,
        "cover_letter": "",
        "error": None,
    }

    try:
        result = await cover_letter_pipeline.ainvoke(initial_state)
    except Exception as exc:
        logger.error("Cover letter pipeline failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cover letter generation failed: {exc}",
        )

    cover_letter_text = result.get("cover_letter", "")
    error = result.get("error")

    if error or not cover_letter_text:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error or "Failed to generate cover letter",
        )

    # Persist to database
    cl_record = CoverLetterModel(
        user_id=user.id,
        resume_id=request.resume_id,
        job_id=request.job_id,
        job_title=request.job_title,
        company_name=request.company_name,
        tone=request.tone,
        content=cover_letter_text,
    )
    db.add(cl_record)
    await db.commit()
    await db.refresh(cl_record)

    return {
        "id": str(cl_record.id),
        "job_title": request.job_title,
        "company_name": request.company_name,
        "tone": request.tone,
        "content": cover_letter_text,
        "generated_at": cl_record.created_at.isoformat(),
    }


# ── Get cover letter by ID ───────────────────────────────────────────────────


@router.get("/{cover_letter_id}")
async def get_cover_letter(
    cover_letter_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a previously generated cover letter."""
    result = await db.execute(
        select(CoverLetterModel).where(
            CoverLetterModel.id == cover_letter_id,
            CoverLetterModel.user_id == user.id,
        )
    )
    cl = result.scalar_one_or_none()
    if cl is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cover letter not found",
        )

    return {
        "id": str(cl.id),
        "job_title": cl.job_title,
        "company_name": cl.company_name,
        "tone": cl.tone,
        "content": cl.content,
        "generated_at": cl.created_at.isoformat(),
    }


# ── List all cover letters ───────────────────────────────────────────────────


@router.get("")
async def list_cover_letters(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all cover letters for the current user."""
    result = await db.execute(
        select(CoverLetterModel)
        .where(CoverLetterModel.user_id == user.id)
        .order_by(CoverLetterModel.created_at.desc())
    )
    letters = result.scalars().all()

    return {
        "cover_letters": [
            {
                "id": str(cl.id),
                "job_title": cl.job_title,
                "company_name": cl.company_name,
                "tone": cl.tone,
                "content": cl.content[:200] + "..." if len(cl.content or "") > 200 else cl.content,
                "generated_at": cl.created_at.isoformat(),
            }
            for cl in letters
        ],
        "total": len(letters),
    }

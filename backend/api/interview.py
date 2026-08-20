"""Interview session endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import Interview
from backend.core.schemas import UserProfile
from backend.db.session import get_db
from backend.security.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/interviews")


# ── Start interview session ──────────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
async def start_interview(
    job_id: UUID,
    resume_id: UUID,
    category: str = "technical",
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.graphs.interview_graph import interview_pipeline

    result = await interview_pipeline.ainvoke(
        {
            "user_id": user.id,
            "job_id": job_id,
            "resume_id": resume_id,
        }
    )
    questions = result.get("questions", [])

    interview = Interview(
        user_id=user.id,
        job_id=job_id,
        resume_version_id=resume_id,
        questions=[q if isinstance(q, dict) else q.model_dump() for q in questions],
    )
    db.add(interview)
    await db.commit()

    return {
        "session_id": str(interview.id),
        "questions": questions,
        "total_questions": len(questions),
    }


# ── Get session ──────────────────────────────────────────────────────────────


@router.get("/{session_id}")
async def get_session(
    session_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Interview).where(
            Interview.id == session_id,
            Interview.user_id == user.id,
        )
    )
    interview = result.scalar_one_or_none()
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {
        "session_id": str(interview.id),
        "job_id": str(interview.job_id),
        "questions": interview.questions,
        "answers": interview.answers,
        "overall_score": interview.overall_score,
        "created_at": interview.created_at.isoformat(),
    }


# ── Submit answer ────────────────────────────────────────────────────────────


@router.post("/{session_id}/answer")
async def submit_answer(
    session_id: UUID,
    question_index: int,
    answer: str,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Interview).where(
            Interview.id == session_id,
            Interview.user_id == user.id,
        )
    )
    interview = result.scalar_one_or_none()
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    answers = interview.answers or {}
    answers[str(question_index)] = answer
    interview.answers = answers
    await db.commit()

    return {"session_id": str(interview.id), "question_index": question_index, "recorded": True}


# ── Get feedback ─────────────────────────────────────────────────────────────


@router.get("/{session_id}/feedback")
async def get_feedback(
    session_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Interview).where(
            Interview.id == session_id,
            Interview.user_id == user.id,
        )
    )
    interview = result.scalar_one_or_none()
    if interview is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if not interview.feedback:
        # Generate feedback on-demand
        from backend.services.llm_service import ModelRouter, TaskCategory

        llm = ModelRouter()
        prompt = (
            f"Evaluate the following interview answers and provide detailed feedback.\n\n"
            f"QUESTIONS AND ANSWERS:\n"
        )
        for i, q in enumerate(interview.questions or []):
            q_text = q.get("question", str(q)) if isinstance(q, dict) else str(q)
            a_text = interview.answers.get(str(i), "No answer provided")
            prompt += f"Q{i+1}: {q_text}\nA{i+1}: {a_text}\n\n"

        feedback_text = await llm.complete(
            messages=[{"role": "user", "content": prompt}],
            category=TaskCategory.CHAT,
        )
        interview.feedback = {"overall_feedback": str(feedback_text)}
        interview.overall_score = 0.0  # would be parsed from LLM output in production
        await db.commit()

    return {
        "session_id": str(interview.id),
        "feedback": interview.feedback,
        "overall_score": interview.overall_score,
    }

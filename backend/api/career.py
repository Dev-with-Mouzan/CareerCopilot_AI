"""Career planning, market intelligence, and skill-gap endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import CareerPlan as CareerPlanModel, MarketSnapshot
from backend.core.schemas import CareerPlan, MarketSnapshot as MarketSnapshotSchema, UserProfile
from backend.db.session import get_db
from backend.security.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/career")


# ── Get career plan ──────────────────────────────────────────────────────────


@router.get("/plan")
async def get_plan(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CareerPlanModel)
        .where(CareerPlanModel.user_id == user.id)
        .order_by(CareerPlanModel.created_at.desc())
        .limit(1)
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        return {"plan": None, "message": "No career plan found. POST /api/career/plan to generate one."}
    return {"plan": plan.plan_data, "target_role": plan.target_role, "created_at": plan.created_at.isoformat()}


# ── Generate career plan ─────────────────────────────────────────────────────


@router.post("/plan", status_code=status.HTTP_201_CREATED)
async def generate_plan(
    target_role: str = "Software Engineer",
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.graphs.career_graph import career_pipeline

    result = await career_pipeline.ainvoke(
        {
            "user_id": user.id,
            "target_role": target_role,
        }
    )
    return {"plan": result.get("plan", {}), "target_role": target_role}


# ── Market intelligence ──────────────────────────────────────────────────────


@router.get("/market")
async def get_market_intelligence(
    target_role: str = "Software Engineer",
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MarketSnapshot)
        .where(MarketSnapshot.target_role == target_role)
        .order_by(MarketSnapshot.generated_at.desc())
        .limit(1)
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        return {"market": None, "message": "No market data available yet."}
    return {
        "target_role": snapshot.target_role,
        "skill_frequency": snapshot.skill_frequency,
        "seniority_distribution": snapshot.seniority_distribution,
        "salary_distribution": snapshot.salary_distribution,
        "remote_percentage": snapshot.remote_percentage,
        "technology_trends": snapshot.technology_trends,
        "generated_at": snapshot.generated_at.isoformat(),
    }


# ── Skill gap analysis ───────────────────────────────────────────────────────


@router.get("/skill-gaps")
async def get_skill_gaps(
    target_role: str = "Software Engineer",
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from backend.services.skill_gap_engine import analyze_skill_gaps
    from backend.services.market_analyzer import analyze_market

    # Get user's resume skills from DB
    from backend.core.models import Resume
    from sqlalchemy import select
    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc()).limit(1)
    )
    resume = resume_result.scalar_one_or_none()
    resume_skills = []
    if resume and resume.parsed_profile:
        resume_skills = [s.get("name", "") for s in resume.parsed_profile.get("skills", []) if isinstance(s, dict)]

    # Get market data for target role
    market = analyze_market(jobs=[], target_role=target_role)
    market_skills = market.skill_frequency if hasattr(market, 'skill_frequency') else {}

    # Derive role-required skills from market data
    role_skills = list(market_skills.keys())[:20] if market_skills else []

    gaps = analyze_skill_gaps(resume_skills, role_skills, market_skills)
    return {"skill_gaps": [g.model_dump() for g in gaps], "target_role": target_role}

"""LangGraph StateGraph for career planning.

Workflow:
    analyze_current_state -> analyze_market -> identify_gaps ->
    generate_learning_plan -> generate_projects -> generate_timeline ->
    generate_application_strategy -> synthesize_plan

Uses market data, skill gaps, and resume profile. LLM for strategic reasoning only.
"""

from __future__ import annotations

import logging
from typing import Literal

from langgraph.graph import END, START, StateGraph

from backend.core.schemas import CareerPlan, SkillGap
from backend.core.state import CareerState
from backend.services.llm_service import ModelRouter, TaskCategory
from backend.services.market_analyzer import analyze_market
from backend.services.skill_gap_engine import analyze_skill_gaps

logger = logging.getLogger(__name__)

_router = ModelRouter()


# ── Nodes ──────────────────────────────────────────────────────────────────────


async def analyze_current_state_node(state: CareerState) -> dict:
    """Analyze the user's current career position from their resume profile."""
    profile_data = state.get("resume_profile", {})

    summary_parts = []
    if profile_data.get("skills"):
        skill_names = [s.get("name", "") for s in profile_data["skills"] if isinstance(s, dict)]
        summary_parts.append(f"Skills: {', '.join(skill_names[:15])}")

    if profile_data.get("experience"):
        exp = profile_data["experience"]
        summary_parts.append(f"Experience entries: {len(exp)}")
        if exp:
            latest = exp[0] if isinstance(exp[0], dict) else {}
            summary_parts.append(f"Current/Recent role: {latest.get('title', 'N/A')}")

    if profile_data.get("years_experience"):
        summary_parts.append(f"Years: {profile_data['years_experience']}")

    if profile_data.get("education"):
        summary_parts.append(f"Education: {len(profile_data['education'])} entries")

    return {"market_data": {"_current_state_summary": "\n".join(summary_parts)}}


async def analyze_market_node(state: CareerState) -> dict:
    """Analyze market data for the target role."""
    target_role = state.get("target_role", "")
    market = analyze_market(jobs=[], target_role=target_role)
    return {"market_data": {**market.model_dump(), "_target_role": target_role}}


async def identify_gaps_node(state: CareerState) -> dict:
    """Identify skill gaps between resume and target role."""
    profile_data = state.get("resume_profile", {})
    market_data = state.get("market_data", {})

    resume_skills = [
        s.get("name", "")
        for s in profile_data.get("skills", [])
        if isinstance(s, dict)
    ]
    role_skills = list(market_data.get("skill_frequency", {}).keys())[:20]
    market_skills = market_data.get("skill_frequency", {})

    gaps = analyze_skill_gaps(resume_skills, role_skills, market_skills)
    return {"skill_gaps": [gap.model_dump() for gap in gaps]}


async def generate_learning_plan_node(state: CareerState) -> dict:
    """Use LLM to generate a prioritized learning plan, with a deterministic fallback."""
    gaps = state.get("skill_gaps", [])
    target_role = state.get("target_role", "")
    top_gaps = [g for g in gaps if isinstance(g, dict) and g.get("priority", 99) <= 3][:10]

    if not top_gaps:
        fallback = [
            f"Map out the core skills required for {target_role} and identify your gaps",
            f"Pick one flagship project to build for your {target_role} portfolio",
            f"Contribute to an open-source project relevant to {target_role}",
            f"Practice {target_role} interview questions weekly",
        ]
        return {"plan": {"learning_priorities": fallback}}

    gap_summary = "\n".join(
        f"- {g.get('skill', 'N/A')} (demand: {g.get('market_demand', 'N/A')}, priority: {g.get('priority', 'N/A')})"
        for g in top_gaps
    )

    prompt = (
        f"Target role: {target_role}\n"
        f"Top skill gaps:\n{gap_summary}\n\n"
        "Create a prioritized learning plan with specific resources, courses, or projects "
        "for each gap. Format as a numbered list."
    )

    try:
        result = await _router.complete(
            messages=[{"role": "user", "content": prompt}],
            category=TaskCategory.CAREER_STRATEGY,
        )
        return {"plan": {"learning_priorities": [str(result)]}}
    except Exception as exc:
        logger.error("LLM learning plan failed: %s", exc)
        raise RuntimeError(f"Failed to generate learning plan: {exc}") from exc


async def generate_projects_node(state: CareerState) -> dict:
    """Use LLM to suggest portfolio projects that address skill gaps."""
    gaps = state.get("skill_gaps", [])
    target_role = state.get("target_role", "")
    top_skills = [g.get("skill", "") for g in gaps if isinstance(g, dict)][:5]

    prompt = (
        f"Target role: {target_role}\n"
        f"Skills to demonstrate: {', '.join(top_skills)}\n\n"
        "Suggest 3 portfolio projects that would showcase these skills. "
        "For each project, provide: name, brief description, and technologies used."
    )

    try:
        result = await _router.complete(
            messages=[{"role": "user", "content": prompt}],
            category=TaskCategory.CAREER_STRATEGY,
        )
        plan = state.get("plan", {})
        return {"plan": {**plan, "projects_suggestion": str(result)}}
    except Exception as exc:
        logger.error("LLM project suggestion failed: %s", exc)
        raise RuntimeError(f"Failed to generate project suggestions: {exc}") from exc


async def generate_timeline_node(state: CareerState) -> dict:
    """Generate a realistic timeline for the career transition."""
    gaps = state.get("skill_gaps", [])
    high_priority = [g for g in gaps if isinstance(g, dict) and g.get("priority", 99) <= 2]
    months = max(len(high_priority) * 2, 3)

    timeline = {
        "immediate": "Update resume and LinkedIn with target role keywords",
        "month_1_2": "Complete top 2 priority skill courses",
        "month_3_4": "Build portfolio projects demonstrating new skills",
        "month_5_6": "Begin active job applications and networking",
        "total_estimated_months": str(months),
    }

    plan = state.get("plan", {})
    return {"plan": {**plan, "timeline": timeline}}


async def generate_application_strategy_node(state: CareerState) -> dict:
    """Use LLM to generate an application strategy."""
    target_role = state.get("target_role", "")
    market = state.get("market_data", {})
    remote_pct = market.get("remote_percentage", 0)
    salary = market.get("salary_distribution", {})

    prompt = (
        f"Target role: {target_role}\n"
        f"Remote job availability: {remote_pct}%\n"
        f"Salary range: ${salary.get('min', 'N/A')} - ${salary.get('max', 'N/A')}\n\n"
        "Provide a concise application strategy covering: "
        "where to apply, how to stand out, networking tips, and timing."
    )

    try:
        result = await _router.complete(
            messages=[{"role": "user", "content": prompt}],
            category=TaskCategory.CAREER_STRATEGY,
        )
        plan = state.get("plan", {})
        return {"plan": {**plan, "application_strategy": str(result)}}
    except Exception as exc:
        logger.error("LLM strategy failed: %s", exc)
        raise RuntimeError(f"Failed to generate application strategy: {exc}") from exc


async def synthesize_plan_node(state: CareerState) -> dict:
    """Assemble the final CareerPlan from all computed components."""
    plan_data = state.get("plan", {})
    gaps = state.get("skill_gaps", [])
    market = state.get("market_data", {})

    career_plan = CareerPlan(
        current_state=market.get("_current_state_summary", ""),
        target_state=f"Transition to {state.get('target_role', 'target role')}",
        skill_gaps=[SkillGap(**g) for g in gaps if isinstance(g, dict)],
        learning_priorities=plan_data.get("learning_priorities", []),
        timeline=plan_data.get("timeline", {}),
        interview_prep="Focus on behavioral + technical questions for target role",
        application_strategy=plan_data.get("application_strategy", ""),
    )

    logger.info(
        "Career plan synthesized: %d skill gaps, target=%s",
        len(career_plan.skill_gaps),
        state.get("target_role"),
    )

    return {"plan": career_plan.model_dump()}


async def error_node(state: CareerState) -> dict:
    """Handle pipeline errors."""
    logger.error("Career pipeline failed for user=%s", state.get("user_id"))
    return {"plan": CareerPlan().model_dump()}


# ── Routing ────────────────────────────────────────────────────────────────────


def route_after_gaps(state: CareerState) -> str:
    """Always proceed to learning plan generation.

    Empty gaps are a normal case (e.g. no market data yet) — not a failure.
    """
    return "generate_learning_plan"


# ── Graph ──────────────────────────────────────────────────────────────────────


def build_career_graph() -> StateGraph:
    """Construct the career planning workflow."""
    graph = StateGraph(CareerState)

    graph.add_node("analyze_current_state", analyze_current_state_node)
    graph.add_node("analyze_market", analyze_market_node)
    graph.add_node("identify_gaps", identify_gaps_node)
    graph.add_node("generate_learning_plan", generate_learning_plan_node)
    graph.add_node("generate_projects", generate_projects_node)
    graph.add_node("generate_timeline", generate_timeline_node)
    graph.add_node("generate_application_strategy", generate_application_strategy_node)
    graph.add_node("synthesize_plan", synthesize_plan_node)
    graph.add_node("error_node", error_node)

    graph.add_edge(START, "analyze_current_state")
    graph.add_edge("analyze_current_state", "analyze_market")
    graph.add_edge("analyze_market", "identify_gaps")
    graph.add_conditional_edges(
        "identify_gaps",
        route_after_gaps,
        {"generate_learning_plan": "generate_learning_plan", "error_node": "error_node"},
    )
    graph.add_edge("generate_learning_plan", "generate_projects")
    graph.add_edge("generate_projects", "generate_timeline")
    graph.add_edge("generate_timeline", "generate_application_strategy")
    graph.add_edge("generate_application_strategy", "synthesize_plan")
    graph.add_edge("synthesize_plan", END)
    graph.add_edge("error_node", END)

    return graph


# Compiled graph instance
career_pipeline = build_career_graph().compile()

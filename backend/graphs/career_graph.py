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
        "Create a prioritized learning plan. For EACH skill gap, provide:\n"
        "1. The specific skill to learn\n"
        "2. A concrete resource (course, book, or tutorial name)\n"
        "3. A hands-on project or exercise to practice it\n\n"
        "Format each item as a single concise line: 'Skill — Resource — Practice method'\n"
        "Keep it actionable and specific. No generic advice."
    )

    try:
        result = await _router.complete(
            messages=[{"role": "user", "content": prompt}],
            category=TaskCategory.CAREER_STRATEGY,
        )
        # Split LLM response into individual items
        raw = str(result).strip()
        items = [line.strip("0123456789. )-\t") for line in raw.split("\n") if line.strip() and len(line.strip()) > 10]
        return {"plan": {"learning_priorities": items or [raw]}}
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
        f"Skills to master: {', '.join(top_skills)}\n\n"
        "Suggest 3 progressive projects to build expertise in this field. "
        "For each project, provide: name, what you'll learn, and technologies used. "
        "Start with a foundational project and increase in complexity."
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
    target_role = state.get("target_role", "")
    high_priority = [g for g in gaps if isinstance(g, dict) and g.get("priority", 99) <= 2]
    all_gaps = [g for g in gaps if isinstance(g, dict)]
    months = max(len(high_priority) * 2, 3)

    # Build skill names for timeline context
    gap_skills = [g.get("skill", "") for g in all_gaps[:5]]
    skills_str = ", ".join(filter(None, gap_skills)) or "core skills"

    timeline = {
        "phase_1_weeks_1_2": f"Update resume, LinkedIn, and portfolio with {target_role} keywords. Audit current skills vs. requirements.",
        "phase_2_weeks_3_8": f"Deep-dive into top priority gaps: {skills_str}. Complete courses, certifications, or tutorials.",
        "phase_3_weeks_9_14": f"Build 2-3 portfolio projects demonstrating {target_role} competencies. Contribute to open source if applicable.",
        "phase_4_weeks_15_20": f"Begin targeted applications to {target_role} roles. Network with professionals in the field.",
        "phase_5_weeks_21_plus": "Interview preparation, mock interviews, and iterative application refinement.",
        "total_estimated_months": str(months),
    }

    plan = state.get("plan", {})
    return {"plan": {**plan, "timeline": timeline}}


async def generate_expertise_milestones_node(state: CareerState) -> dict:
    """Use LLM to generate expertise milestones for the target field."""
    target_role = state.get("target_role", "")
    gaps = state.get("skill_gaps", [])
    top_skills = [g.get("skill", "") for g in gaps if isinstance(g, dict)][:5]

    prompt = (
        f"Target field: {target_role}\n"
        f"Key skills to master: {', '.join(top_skills)}\n\n"
        "Create 4-6 concrete expertise milestones for mastering this field. "
        "Each milestone should be a measurable achievement, not just 'learn X'. "
        "Cover: fundamentals, intermediate depth, advanced projects, and real-world application.\n\n"
        "Format as a numbered list. Be specific to this field, not generic."
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


async def generate_roadmap_node(state: CareerState) -> dict:
    """Use LLM to generate a phased technology/language/platform roadmap.

    Falls back to a deterministic roadmap derived from skill gaps when the
    LLM call fails, so the career tab always renders a usable roadmap.
    """
    target_role = state.get("target_role", "")
    gaps = state.get("skill_gaps", [])
    gap_skills = [g.get("skill", "") for g in gaps if isinstance(g, dict)]
    skills_str = ", ".join(filter(None, gap_skills[:8])) or "core skills for the role"

    prompt = (
        f"Target role: {target_role}\n"
        f"Skills to master: {skills_str}\n\n"
        "Create a learning roadmap with 3 phases (foundation, intermediate, advanced). "
        "For EACH phase, list exactly three groups as plain lines using these prefixes:\n"
        "TECHNOLOGIES: <comma-separated technologies/tools/frameworks to learn>\n"
        "LANGUAGES: <comma-separated programming languages to learn>\n"
        "PLATFORMS: <comma-separated platforms whose internal working must be understood>\n"
        "Then end the phase with a line 'WHY: <one sentence on why this phase matters>'.\n"
        "Keep each list to 4-6 items. Be specific to the role, not generic."
    )

    try:
        result = await _router.complete(
            messages=[{"role": "user", "content": prompt}],
            category=TaskCategory.CAREER_STRATEGY,
        )
        roadmap = _parse_roadmap_text(str(result))
    except Exception as exc:
        logger.warning("LLM roadmap failed, using fallback: %s", exc)
        roadmap = _fallback_roadmap(target_role, gap_skills)

    if not roadmap:
        roadmap = _fallback_roadmap(target_role, gap_skills)

    plan = state.get("plan", {})
    return {"plan": {**plan, "roadmap": roadmap}}


def _parse_roadmap_text(raw: str) -> list[dict]:
    """Parse the LLM's phased roadmap text into structured phases."""
    phases: list[dict] = []
    current: dict | None = None

    def _flush() -> None:
        nonlocal current
        if current and (current["technologies"] or current["languages"] or current["platforms"]):
            phases.append(current)
        current = None

    for line in raw.splitlines():
        line = line.strip().lstrip("#*- ")
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith(("phase", "stage", "level", "step")) and ":" in line:
            _flush()
            current = {
                "name": line.split(":", 1)[0].strip(),
                "technologies": [],
                "languages": [],
                "platforms": [],
                "why": "",
            }
            continue
        if current is None:
            continue
        if lowered.startswith("technologies:"):
            current["technologies"] = _split_list(line[len("technologies:"):])
        elif lowered.startswith("languages:"):
            current["languages"] = _split_list(line[len("languages:"):])
        elif lowered.startswith("platforms:"):
            current["platforms"] = _split_list(line[len("platforms:"):])
        elif lowered.startswith("why:"):
            current["why"] = line[len("why:"):].strip()
    _flush()
    return phases


def _split_list(value: str) -> list[str]:
    """Split a comma-separated list and trim markdown/numbering noise."""
    items = [i.strip(" -*#").strip() for i in value.split(",")]
    return [i for i in items if i][:8]


def _fallback_roadmap(target_role: str, gap_skills: list[str]) -> list[dict]:
    """Deterministic 3-phase roadmap when the LLM is unavailable."""
    skills = [s for s in gap_skills if s][:6] or ["fundamentals"]
    return [
        {
            "name": "Phase 1 — Foundation",
            "technologies": skills[:2],
            "languages": ["Python or JavaScript"],
            "platforms": ["Linux basics", "Git & GitHub"],
            "why": "Build core fundamentals before specializing.",
        },
        {
            "name": "Phase 2 — Intermediate",
            "technologies": skills[2:4] or ["databases"],
            "languages": ["SQL"],
            "platforms": ["How web servers work", "How databases work"],
            "why": "Apply skills by building real projects end-to-end.",
        },
        {
            "name": "Phase 3 — Advanced",
            "technologies": skills[4:6] or ["cloud services"],
            "languages": ["Go or Rust (optional depth)"],
            "platforms": ["How cloud platforms work", "How CI/CD pipelines work"],
            "why": "Reach production-grade depth expected for the role.",
        },
    ]


async def synthesize_plan_node(state: CareerState) -> dict:
    """Assemble the final CareerPlan from all computed components."""
    plan_data = state.get("plan", {})
    gaps = state.get("skill_gaps", [])
    market = state.get("market_data", {})

    # Build structured projects from LLM text if available
    projects_text = plan_data.get("projects_suggestion", "")

    career_plan = CareerPlan(
        current_state=market.get("_current_state_summary", ""),
        target_state=f"Master {state.get('target_role', 'target field')}",
        skill_gaps=[SkillGap(**g) for g in gaps if isinstance(g, dict)],
        learning_priorities=plan_data.get("learning_priorities", []),
        timeline=plan_data.get("timeline", {}),
        interview_prep="",
        application_strategy=plan_data.get("expertise_milestones", ""),
    )

    plan_dict = career_plan.model_dump()
    # Attach raw projects text for frontend rendering
    if projects_text:
        plan_dict["projects_suggestion"] = projects_text
    # Attach structured roadmap (technologies/languages/platforms per phase)
    roadmap = plan_data.get("roadmap", [])
    if roadmap:
        plan_dict["roadmap"] = roadmap

    plan_dict = career_plan.model_dump()
    # Attach raw projects text for frontend rendering
    if projects_text:
        plan_dict["projects_suggestion"] = projects_text

    logger.info(
        "Career plan synthesized: %d skill gaps, target=%s",
        len(career_plan.skill_gaps),
        state.get("target_role"),
    )

    return {"plan": plan_dict}


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
    graph.add_node("generate_roadmap", generate_roadmap_node)
    graph.add_node("generate_expertise_milestones", generate_expertise_milestones_node)
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
    graph.add_edge("generate_timeline", "generate_roadmap")
    graph.add_edge("generate_roadmap", "generate_expertise_milestones")
    graph.add_edge("generate_expertise_milestones", "synthesize_plan")
    graph.add_edge("synthesize_plan", END)
    graph.add_edge("error_node", END)

    return graph


# Compiled graph instance
career_pipeline = build_career_graph().compile()

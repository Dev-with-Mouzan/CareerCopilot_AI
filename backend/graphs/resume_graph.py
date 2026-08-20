"""LangGraph StateGraph for resume parsing and profile building.

Workflow:
    parse_resume -> extract_text -> detect_sections -> build_profile -> generate_embedding -> store_resume

All nodes are deterministic (no LLM). Conditional edges handle parsing failures.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

from langgraph.graph import END, START, StateGraph

from backend.core.schemas import ResumeProfile
from backend.core.state import ResumeState
from backend.services.embeddings import generate_embedding
from backend.services.resume_parser import parse_resume

logger = logging.getLogger(__name__)


# ── Nodes ──────────────────────────────────────────────────────────────────────


async def parse_resume_node(state: ResumeState) -> dict:
    """Extract text from the resume file and parse into structured sections."""
    resume_id = str(state["resume_id"])
    user_id = str(state["user_id"])

    file_path = Path("storage") / user_id / f"{resume_id}"
    # Try common extensions
    for ext in (".pdf", ".docx", ".txt"):
        candidate = file_path.with_suffix(ext)
        if candidate.exists():
            file_path = candidate
            break
    else:
        return {
            "parsing_status": "failed",
            "error": f"No resume file found for user={user_id} resume={resume_id}",
        }

    try:
        profile = parse_resume(file_path)
        return {
            "resume_text": file_path.read_text(encoding="utf-8", errors="replace"),
            "resume_profile": profile.model_dump(),
            "parsing_status": "completed",
            "error": None,
        }
    except Exception as exc:
        logger.error("Resume parsing failed: %s", exc)
        return {"parsing_status": "failed", "error": str(exc)}


async def extract_text_node(state: ResumeState) -> dict:
    """Validate that resume text was successfully extracted."""
    if not state.get("resume_text"):
        return {"parsing_status": "failed", "error": "No text extracted from resume"}
    return {}


async def detect_sections_node(state: ResumeState) -> dict:
    """Validate that the profile has meaningful sections."""
    profile_data = state.get("resume_profile", {})
    skills = profile_data.get("skills", [])
    experience = profile_data.get("experience", [])

    if not skills and not experience:
        return {
            "parsing_status": "failed",
            "error": "Resume contains no recognizable skills or experience sections",
        }
    return {}


async def build_profile_node(state: ResumeState) -> dict:
    """Enrich the profile with computed fields (years of experience, target roles)."""
    profile_data = state.get("resume_profile", {})
    profile = ResumeProfile(**profile_data)

    # Compute years of experience from experience entries
    if profile.experience:
        from datetime import date

        earliest = min(e.start_date for e in profile.experience)
        latest_end = max(
            (e.end_date or date.today()), default=date.today()
        )
        years = round((latest_end - earliest).days / 365.25, 1)
        profile.years_experience = years

    # Infer target roles from experience titles
    title_keywords: dict[str, list[str]] = {
        "engineer": ["software engineer", "backend engineer", "frontend engineer", "full stack engineer"],
        "developer": ["web developer", "mobile developer", "full stack developer"],
        "scientist": ["data scientist", "ml scientist"],
        "analyst": ["data analyst", "business analyst"],
        "architect": ["solution architect", "cloud architect"],
        "manager": ["engineering manager", "product manager", "technical manager"],
        "designer": ["ui designer", "ux designer", "product designer"],
    }

    roles: set[str] = set()
    for exp in profile.experience:
        title_lower = exp.title.lower()
        for keyword, role_list in title_keywords.items():
            if keyword in title_lower:
                roles.update(role_list)
    profile.target_roles = list(roles)[:5] if roles else ["software engineer"]

    return {"resume_profile": profile.model_dump()}


async def generate_embedding_node(state: ResumeState) -> dict:
    """Generate a vector embedding of the resume for similarity search."""
    profile_data = state.get("resume_profile", {})
    profile = ResumeProfile(**profile_data)

    # Build a text representation for embedding
    parts = [profile.summary] if profile.summary else []
    parts.extend(s.name for s in profile.skills)
    parts.extend(f"{e.title} {e.company} {e.description[:200]}" for e in profile.experience)
    text_for_embedding = " ".join(parts)

    if not text_for_embedding.strip():
        return {}

    try:
        embedding = generate_embedding(text_for_embedding)
        return {"resume_profile": {**profile_data, "_embedding": embedding}}
    except Exception as exc:
        logger.warning("Embedding generation failed: %s", exc)
        return {}


async def store_resume_node(state: ResumeState) -> dict:
    """Store the final resume profile (placeholder for DB persistence)."""
    profile_data = state.get("resume_profile", {})
    logger.info(
        "Storing resume profile for user=%s resume=%s (skills=%d, experience=%d)",
        state["user_id"],
        state["resume_id"],
        len(profile_data.get("skills", [])),
        len(profile_data.get("experience", [])),
    )
    return {}


async def error_node(state: ResumeState) -> dict:
    """Handle parsing errors — log and finalize status."""
    logger.error(
        "Resume pipeline failed for user=%s resume=%s: %s",
        state["user_id"],
        state["resume_id"],
        state.get("error", "unknown"),
    )
    return {"parsing_status": "failed"}


# ── Routing ────────────────────────────────────────────────────────────────────


def route_after_parse(state: ResumeState) -> Literal["extract_text", "error_node"]:
    """Branch on whether parsing succeeded."""
    if state.get("parsing_status") == "failed":
        return "error_node"
    return "extract_text"


def route_after_sections(state: ResumeState) -> Literal["build_profile", "error_node"]:
    """Branch on whether sections were detected."""
    if state.get("parsing_status") == "failed":
        return "error_node"
    return "build_profile"


# ── Graph ──────────────────────────────────────────────────────────────────────


def build_resume_graph() -> StateGraph:
    """Construct the resume processing workflow."""
    graph = StateGraph(ResumeState)

    # Add nodes
    graph.add_node("parse_resume", parse_resume_node)
    graph.add_node("extract_text", extract_text_node)
    graph.add_node("detect_sections", detect_sections_node)
    graph.add_node("build_profile", build_profile_node)
    graph.add_node("generate_embedding", generate_embedding_node)
    graph.add_node("store_resume", store_resume_node)
    graph.add_node("error_node", error_node)

    # Edges
    graph.add_edge(START, "parse_resume")
    graph.add_conditional_edges(
        "parse_resume",
        route_after_parse,
        {"extract_text": "extract_text", "error_node": "error_node"},
    )
    graph.add_edge("extract_text", "detect_sections")
    graph.add_conditional_edges(
        "detect_sections",
        route_after_sections,
        {"build_profile": "build_profile", "error_node": "error_node"},
    )
    graph.add_edge("build_profile", "generate_embedding")
    graph.add_edge("generate_embedding", "store_resume")
    graph.add_edge("store_resume", END)
    graph.add_edge("error_node", END)

    return graph


# Compiled graph instance
resume_pipeline = build_resume_graph().compile()

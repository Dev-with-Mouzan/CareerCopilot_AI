"""Tests for backend.graphs.resume_graph — LangGraph state machine execution."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from backend.core.state import ResumeState


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def base_state() -> ResumeState:
    return {
        "user_id": uuid4(),
        "resume_id": uuid4(),
        "resume_version_id": uuid4(),
        "resume_text": "",
        "resume_profile": {},
        "parsing_status": "pending",
        "error": None,
    }


# ── Graph Construction ────────────────────────────────────────────────────────


class TestBuildGraph:
    def test_builds_graph(self):
        from backend.graphs.resume_graph import build_resume_graph

        graph = build_resume_graph()
        compiled = graph.compile()
        assert compiled is not None

    def test_graph_has_nodes(self):
        from backend.graphs.resume_graph import build_resume_graph

        graph = build_resume_graph()
        node_names = list(graph.nodes.keys())
        assert "parse_resume" in node_names
        assert "extract_text" in node_names
        assert "detect_sections" in node_names
        assert "build_profile" in node_names
        assert "generate_embedding" in node_names
        assert "store_resume" in node_names
        assert "error_node" in node_names


# ── Routing Functions ─────────────────────────────────────────────────────────


class TestRouting:
    def test_route_after_parse_success(self):
        from backend.graphs.resume_graph import route_after_parse

        state = {"parsing_status": "completed"}
        assert route_after_parse(state) == "extract_text"

    def test_route_after_parse_failure(self):
        from backend.graphs.resume_graph import route_after_parse

        state = {"parsing_status": "failed"}
        assert route_after_parse(state) == "error_node"

    def test_route_after_sections_success(self):
        from backend.graphs.resume_graph import route_after_sections

        state = {"parsing_status": "completed"}
        assert route_after_sections(state) == "build_profile"

    def test_route_after_sections_failure(self):
        from backend.graphs.resume_graph import route_after_sections

        state = {"parsing_status": "failed"}
        assert route_after_sections(state) == "error_node"


# ── Node Functions ────────────────────────────────────────────────────────────


class TestNodes:
    @pytest.mark.asyncio
    async def test_extract_text_node_no_text(self, base_state):
        from backend.graphs.resume_graph import extract_text_node

        base_state["resume_text"] = ""
        result = await extract_text_node(base_state)
        assert result.get("parsing_status") == "failed"

    @pytest.mark.asyncio
    async def test_extract_text_node_with_text(self, base_state):
        from backend.graphs.resume_graph import extract_text_node

        base_state["resume_text"] = "Some resume content"
        result = await extract_text_node(base_state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_detect_sections_no_skills_no_experience(self, base_state):
        from backend.graphs.resume_graph import detect_sections_node

        base_state["resume_profile"] = {"skills": [], "experience": []}
        result = await detect_sections_node(base_state)
        assert result.get("parsing_status") == "failed"

    @pytest.mark.asyncio
    async def test_detect_sections_with_skills(self, base_state):
        from backend.graphs.resume_graph import detect_sections_node

        base_state["resume_profile"] = {"skills": [{"name": "python"}], "experience": []}
        result = await detect_sections_node(base_state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_detect_sections_with_experience(self, base_state):
        from backend.graphs.resume_graph import detect_sections_node

        base_state["resume_profile"] = {"skills": [], "experience": [{"title": "Engineer"}]}
        result = await detect_sections_node(base_state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_error_node(self, base_state):
        from backend.graphs.resume_graph import error_node

        base_state["error"] = "Something went wrong"
        result = await error_node(base_state)
        assert result["parsing_status"] == "failed"

    @pytest.mark.asyncio
    async def test_store_resume_node(self, base_state):
        from backend.graphs.resume_graph import store_resume_node

        result = await store_resume_node(base_state)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_build_profile_node(self, base_state):
        from backend.graphs.resume_graph import build_profile_node

        base_state["resume_profile"] = {
            "skills": [],
            "experience": [
                {
                    "title": "Software Engineer",
                    "company": "Acme",
                    "start_date": "2020-01-01",
                    "end_date": None,
                    "description": "",
                    "skills_used": [],
                    "is_current": True,
                }
            ],
            "education": [],
            "projects": [],
            "certifications": [],
            "years_experience": 0,
            "summary": "",
            "contact_info": {},
        }
        result = await build_profile_node(base_state)
        assert "resume_profile" in result
        assert result["resume_profile"]["years_experience"] > 0


# ── Compiled Graph Integration ────────────────────────────────────────────────


class TestCompiledGraph:
    def test_compiled_graph_exists(self):
        from backend.graphs.resume_graph import resume_pipeline

        assert resume_pipeline is not None

    @pytest.mark.asyncio
    async def test_graph_runs_with_missing_file(self, base_state):
        """Graph should handle missing file gracefully via error_node."""
        from backend.graphs.resume_graph import resume_pipeline

        # This will fail because the file doesn't exist, but the graph
        # should route to error_node and complete without raising
        base_state["resume_text"] = ""
        base_state["resume_profile"] = {"skills": [], "experience": []}
        base_state["parsing_status"] = "failed"
        base_state["error"] = "No resume file found"

        # The graph should complete (route to error_node -> END)
        # without raising an unhandled exception
        result = await resume_pipeline.ainvoke(base_state)
        assert result.get("parsing_status") == "failed"

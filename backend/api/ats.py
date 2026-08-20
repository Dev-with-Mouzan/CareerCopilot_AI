"""ATS endpoints — stub (requires database for full functionality)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from backend.core.schemas import UserProfile
from backend.security.auth import get_current_user

router = APIRouter(prefix="/ats")


@router.post("/analyze")
async def analyze_ats(user: UserProfile = Depends(get_current_user)):
    return {"error": "ATS analysis requires database storage"}, 501


@router.get("/reports")
async def list_reports(user: UserProfile = Depends(get_current_user)):
    return {"reports": []}


@router.get("/reports/{report_id}")
async def get_report(report_id: uuid.UUID, user: UserProfile = Depends(get_current_user)):
    return {"error": "Report not found"}, 404


@router.post("/optimize")
async def optimize_resume(user: UserProfile = Depends(get_current_user)):
    return {"error": "Optimization requires database storage"}, 501

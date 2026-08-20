"""Chat and conversation endpoints with SSE streaming."""

from __future__ import annotations

import json
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.models import Conversation as ConversationModel, ConversationMessage, Resume
from backend.core.schemas import UserProfile
from backend.db.session import get_db, async_session_factory
from backend.security.auth import get_current_user
from backend.security.sanitization import sanitize_user_input, escape_for_llm

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Send message (SSE stream) ────────────────────────────────────────────────


@router.post("/chat")
async def send_message(
    request: Request,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    body = await request.json()
    message = sanitize_user_input(body.get("message", ""))
    conversation_id = body.get("conversation_id")
    model_override = body.get("model")  # user-selected model from frontend
    api_key_override = body.get("api_key")  # optional user-provided API key

    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

    # Resolve or create conversation
    if conversation_id:
        result = await db.execute(
            select(ConversationModel).where(
                ConversationModel.id == UUID(conversation_id),
                ConversationModel.user_id == user.id,
            )
        )
        conversation = result.scalar_one_or_none()
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        conversation = ConversationModel(user_id=user.id)
        db.add(conversation)
        await db.flush()

    # Store user message
    user_msg = ConversationMessage(
        conversation_id=conversation.id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    await db.commit()

    # Fetch recent messages for context
    hist_result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation.id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(20)
    )
    history = list(reversed(hist_result.scalars().all()))

    # Get resume context
    resume_result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc()).limit(1)
    )
    resume = resume_result.scalar_one_or_none()
    resume_text = (resume.raw_text or "")[:3000] if resume else ""

    # Build prompt
    context_lines = ["You are an expert AI career coach.", ""]
    if resume_text:
        context_lines.append(f"USER RESUME:\n{escape_for_llm(resume_text)}\n")
    if len(history) > 1:
        context_lines.append("CONVERSATION HISTORY:")
        for m in history[:-1]:
            role = "User" if m.role == "user" else "Coach"
            context_lines.append(f"{role}: {m.content}")
        context_lines.append("")
    context_lines.append(f"User: {message}")
    full_prompt = "\n".join(context_lines)

    async def event_stream():
        try:
            from backend.services.llm_service import LLMService

            llm = LLMService()
            full_reply = []
            async for chunk in llm.stream(full_prompt, model=model_override, api_key=api_key_override):
                full_reply.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk, 'conversation_id': str(conversation.id)})}\n\n"

            # Store assistant reply
            reply_text = "".join(full_reply)
            async with async_session_factory() as session:
                msg = ConversationMessage(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=reply_text,
                )
                session.add(msg)
                await session.commit()

            yield f"data: {json.dumps({'done': True, 'conversation_id': str(conversation.id)})}\n\n"
        except Exception as exc:
            logger.exception("Chat stream error")
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── List conversations ───────────────────────────────────────────────────────


@router.get("/conversations")
async def list_conversations(
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    result = await db.execute(
        select(ConversationModel)
        .where(ConversationModel.user_id == user.id)
        .order_by(ConversationModel.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = result.scalars().all()
    return {
        "conversations": [
            {
                "id": str(c.id),
                "summary": c.summary,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in rows
        ],
        "offset": offset,
        "limit": limit,
    }


# ── Get conversation with messages ──────────────────────────────────────────


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConversationModel)
        .options(selectinload(ConversationModel.messages))
        .where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return {
        "id": str(conversation.id),
        "summary": conversation.summary,
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "tools_used": m.tools_used,
                "created_at": m.created_at.isoformat(),
            }
            for m in sorted(conversation.messages, key=lambda x: x.created_at)
        ],
    }


# ── Delete conversation ──────────────────────────────────────────────────────


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    user: UserProfile = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user.id,
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.delete(conversation)
    await db.commit()

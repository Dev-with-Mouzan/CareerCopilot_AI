"""Centralized LLM service — model routing, structured output, caching, cost tracking."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from enum import Enum
from typing import Any, TypeVar

import litellm
from pydantic import BaseModel

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ── Cost estimates per 1 M tokens (USD) ─────────────────────────────────────

_COST_TABLE: dict[str, dict[str, float]] = {
    # Gemini
    "gemini/gemini-2.5-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini/gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    # Groq
    "groq/llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "groq/llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "groq/mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
    # OpenAI
    "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai/gpt-4o": {"input": 2.50, "output": 10.0},
    "openai/gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "openai/gpt-4.1-nano": {"input": 0.10, "output": 0.40},
    # DeepSeek
    "deepseek/deepseek-chat": {"input": 0.27, "output": 1.10},
    "deepseek/deepseek-reasoner": {"input": 0.55, "output": 2.19},
    # Qwen (via OpenAI-compatible API)
    "openai/qwen-turbo": {"input": 0.05, "output": 0.20},
    "openai/qwen-plus": {"input": 0.40, "output": 1.20},
    "openai/qwen-max": {"input": 1.60, "output": 6.40},
}


class TaskCategory(str, Enum):
    EXTRACTION = "extraction"
    CHAT = "chat"
    ATS_EXPLANATION = "ats_explanation"
    RESUME_REWRITE = "resume_rewrite"
    CAREER_STRATEGY = "career_strategy"


# Category → preferred model tier
_TASK_MODEL_MAP: dict[TaskCategory, str] = {
    TaskCategory.EXTRACTION: "fast",
    TaskCategory.CHAT: "fast",
    TaskCategory.ATS_EXPLANATION: "strong",
    TaskCategory.RESUME_REWRITE: "strong",
    TaskCategory.CAREER_STRATEGY: "strong",
}


class ModelRouter:
    """Route tasks to the appropriate model and handle fallbacks."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._cache: dict[str, Any] = {}
        self._usage_log: list[dict[str, Any]] = []

    # ── Model selection ────────────────────────────────────────────────────

    def _model_for(self, category: TaskCategory, model_override: str | None = None) -> str:
        if model_override:
            return model_override
        tier = _TASK_MODEL_MAP.get(category, "fast")
        if tier == "strong":
            return self._settings.strong_model
        return self._settings.fast_model

    def _fallback_model(self, failed_model: str) -> str:
        """Return the other tier's model as fallback."""
        settings = self._settings
        if failed_model == settings.fast_model:
            return settings.strong_model
        return settings.fast_model

    # ── Cache ──────────────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(model: str, messages: list[dict[str, str]], temperature: float) -> str:
        """Deterministic cache key for identical (model, messages, temperature)."""
        blob = json.dumps(
            {"model": model, "messages": messages, "temperature": temperature},
            sort_keys=True,
        )
        return hashlib.sha256(blob.encode()).hexdigest()

    # ── Core completion ────────────────────────────────────────────────────

    async def complete(
        self,
        *,
        messages: list[dict[str, str]],
        category: TaskCategory = TaskCategory.CHAT,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: type[BaseModel] | None = None,
        use_cache: bool = True,
    ) -> str | BaseModel:
        """Send a completion request with automatic retry and fallback.

        Returns a ``str`` by default, or a validated Pydantic instance when
        *response_format* is provided.
        """
        settings = self._settings
        chosen_model = self._model_for(category, model)
        temp = temperature if temperature is not None else settings.llm_temperature
        tokens = max_tokens or settings.llm_max_tokens

        if use_cache:
            key = self._cache_key(chosen_model, messages, temp)
            if key in self._cache:
                logger.debug("Cache hit for %s", key[:12])
                return self._cache[key]

        # Try primary model, then fallback
        for attempt_model in (chosen_model, self._fallback_model(chosen_model)):
            try:
                result = await self._call_llm(
                    model=attempt_model,
                    messages=messages,
                    temperature=temp,
                    max_tokens=tokens,
                    response_format=response_format,
                )
                if use_cache:
                    self._cache[self._cache_key(chosen_model, messages, temp)] = result
                return result
            except Exception as exc:
                logger.warning(
                    "LLM call failed on %s: %s — trying fallback",
                    attempt_model,
                    exc,
                )

        raise RuntimeError("All LLM models failed")

    async def _call_llm(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: type[BaseModel] | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
    ) -> str | BaseModel:
        """Execute a single litellm completion call."""
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if api_key:
            kwargs["api_key"] = api_key
        if api_base:
            kwargs["api_base"] = api_base

        if response_format is not None:
            kwargs["response_format"] = response_format

        t0 = time.monotonic()
        response = await litellm.acompletion(**kwargs)
        elapsed = time.monotonic() - t0

        # Track usage
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        total_tokens = prompt_tokens + completion_tokens
        cost = self._estimate_cost(model, prompt_tokens, completion_tokens)

        self._usage_log.append(
            {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": cost,
                "elapsed_s": round(elapsed, 3),
            }
        )
        logger.info(
            "LLM %s: %d tokens, $%.4f, %.2fs",
            model,
            total_tokens,
            cost,
            elapsed,
        )

        choice = response.choices[0]  # type: ignore[index]
        content: str = choice.message.content or ""  # type: ignore[union-attr]

        if response_format is not None:
            return response_format.model_validate_json(content)

        return content

    # ── Structured helpers ─────────────────────────────────────────────────

    async def structured(
        self,
        *,
        messages: list[dict[str, str]],
        schema: type[T],
        category: TaskCategory = TaskCategory.EXTRACTION,
        model: str | None = None,
    ) -> T:
        """Convenience wrapper that always returns a validated Pydantic model."""
        result = await self.complete(
            messages=messages,
            category=category,
            model=model,
            response_format=schema,
        )
        if isinstance(result, schema):
            return result
        # Fallback: parse JSON string
        return schema.model_validate_json(str(result))

    # ── Cost ───────────────────────────────────────────────────────────────

    @staticmethod
    def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        rates = _COST_TABLE.get(model, {"input": 1.0, "output": 3.0})
        return (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 1_000_000

    @property
    def total_cost(self) -> float:
        return sum(e["cost_usd"] for e in self._usage_log)

    @property
    def total_tokens(self) -> int:
        return sum(e["total_tokens"] for e in self._usage_log)

    @property
    def usage_log(self) -> list[dict[str, Any]]:
        return list(self._usage_log)

    # ── Streaming ───────────────────────────────────────────────────────────

    @staticmethod
    def _resolve_api_base(model: str) -> str | None:
        """Return the API base URL for models that need one (e.g. Qwen)."""
        if model.startswith("openai/qwen-"):
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        return None

    async def stream(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system: str = "You are an expert AI career coach. Be concise and helpful.",
        temperature: float | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
    ):
        """Yield text chunks from a streaming LLM completion."""
        settings = self._settings
        chosen_model = model or settings.fast_model
        temp = temperature if temperature is not None else settings.llm_temperature
        tokens = max_tokens or settings.llm_max_tokens
        api_base = api_key and self._resolve_api_base(chosen_model)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        kwargs: dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": tokens,
            "stream": True,
        }
        if api_key:
            kwargs["api_key"] = api_key
        if api_base:
            kwargs["api_base"] = api_base

        try:
            response = await litellm.acompletion(**kwargs)
            async for chunk in response:  # type: ignore[union-attr]
                delta = chunk.choices[0].delta if chunk.choices else None  # type: ignore[union-attr]
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            logger.warning("Stream failed on %s: %s — trying fallback", chosen_model, exc)
            fallback = self._fallback_model(chosen_model)
            try:
                fallback_base = self._resolve_api_base(fallback)
                fb_kwargs: dict[str, Any] = {
                    "model": fallback,
                    "messages": messages,
                    "temperature": temp,
                    "max_tokens": tokens,
                    "stream": True,
                }
                if api_key:
                    fb_kwargs["api_key"] = api_key
                if fallback_base:
                    fb_kwargs["api_base"] = fallback_base
                response = await litellm.acompletion(**fb_kwargs)
                async for chunk in response:  # type: ignore[union-attr]
                    delta = chunk.choices[0].delta if chunk.choices else None  # type: ignore[union-attr]
                    if delta and delta.content:
                        yield delta.content
            except Exception as exc2:
                logger.error("All streaming models failed: %s", exc2)
                yield "I'm sorry, I encountered an error. Please try again."


# ── LLMService alias for backward compatibility ─────────────────────────────


class LLMService:
    """Thin wrapper used by the chat endpoint.  Delegates to the global ModelRouter singleton."""

    def __init__(self) -> None:
        # Always use the module-level singleton — never create a new ModelRouter
        global _llm_service
        if _llm_service is None:
            _llm_service = ModelRouter()
        self._router = _llm_service

    async def stream(
        self, prompt: str, *, model: str | None = None, api_key: str | None = None, **kwargs: Any
    ):
        async for chunk in self._router.stream(prompt, model=model, api_key=api_key, **kwargs):
            yield chunk

    async def complete(self, *args: Any, **kwargs: Any) -> str | BaseModel:
        return await self._router.complete(*args, **kwargs)


# ── Module-level singleton ───────────────────────────────────────────────────

_llm_service: ModelRouter | None = None


def get_llm_service() -> ModelRouter:
    """Return (and create on first call) the global ModelRouter singleton."""
    global _llm_service
    if _llm_service is None:
        _llm_service = ModelRouter()
    return _llm_service

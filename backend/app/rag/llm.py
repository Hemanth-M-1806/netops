"""
LLM client abstraction.

Supported providers (set LLM_PROVIDER env var):
  mock    — returns a canned response instantly (default, no API key needed)
  openai  — calls OpenAI-compatible chat completions endpoint
  ollama  — calls local Ollama HTTP API
  local   — generic OpenAI-compatible local server

Adding a new provider:
  1. Add a branch in `_get_client`.
  2. Implement an async `complete(messages) -> str` method.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import Settings
from app.core.errors import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── abstract base ─────────────────────────────────────────────────────────────

class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict[str, str]]) -> tuple[str, int]:
        """
        Parameters
        ----------
        messages : OpenAI-style messages list

        Returns
        -------
        (reply_text, token_count)
        """


# ── Mock (no API key needed) ──────────────────────────────────────────────────

class MockLLMClient(BaseLLMClient):
    async def complete(self, messages: list[dict[str, str]]) -> tuple[str, int]:
        user_msg = next((m["content"] for m in messages if m["role"] == "user"), "?")
        reply = (
            f"[Mock Copilot] I received your question: «{user_msg[:80]}». "
            "Add your LLM_PROVIDER and API key to get real AI-powered responses. "
            "The RAG context has been retrieved from the database and injected into the prompt."
        )
        return reply, len(reply.split())


# ── OpenAI-compatible ─────────────────────────────────────────────────────────

class OpenAIClient(BaseLLMClient):
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.openai_base_url.rstrip("/")
        self._api_key  = settings.openai_api_key
        self._model    = settings.llm_model
        self._temp     = settings.llm_temperature
        self._max_tok  = settings.llm_max_tokens

    async def complete(self, messages: list[dict[str, str]]) -> tuple[str, int]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temp,
            "max_tokens": self._max_tok,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=body,
                    headers=headers,
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise LLMError(f"OpenAI API error {exc.response.status_code}: {exc.response.text[:200]}") from exc
            except httpx.RequestError as exc:
                raise LLMError(f"OpenAI request failed: {exc}") from exc

        data = resp.json()
        reply = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", len(reply.split()))
        return reply, tokens


# ── Ollama ────────────────────────────────────────────────────────────────────

class OllamaClient(BaseLLMClient):
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model    = settings.llm_model
        self._temp     = settings.llm_temperature

    async def complete(self, messages: list[dict[str, str]]) -> tuple[str, int]:
        body = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self._temp},
        }
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                resp = await client.post(f"{self._base_url}/api/chat", json=body)
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise LLMError(f"Ollama error {exc.response.status_code}") from exc
            except httpx.RequestError as exc:
                raise LLMError(f"Ollama request failed: {exc}") from exc

        data = resp.json()
        reply = data["message"]["content"]
        tokens = data.get("eval_count", len(reply.split()))
        return reply, tokens


# ── OpenRouter (Qwen reasoning enabled) ───────────────────────────────────────

class OpenRouterClient(BaseLLMClient):
    def __init__(self, settings: Settings) -> None:
        self._base_url = (settings.openrouter_base_url or "https://openrouter.ai/api/v1").rstrip("/")
        self._api_key  = settings.openrouter_api_key or settings.openai_api_key
        self._model    = settings.llm_model or "qwen/qwen3.8-27b:free"
        self._temp     = settings.llm_temperature
        self._max_tok  = settings.llm_max_tokens

    async def complete(self, messages: list[dict[str, str]]) -> tuple[str, int]:
        import asyncio

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5173",
            "X-Title": "NetOps NOC",
        }
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": self._temp,
            "max_tokens": self._max_tok,
            "reasoning": {"enabled": True},
        }

        max_retries = 3
        last_error = ""

        async with httpx.AsyncClient(timeout=60) as client:
            for attempt in range(max_retries):
                try:
                    resp = await client.post(
                        f"{self._base_url}/chat/completions",
                        json=body,
                        headers=headers,
                    )
                    if resp.status_code == 429:
                        last_error = resp.text
                        logger.warning(f"OpenRouter 429 rate limit (attempt {attempt + 1}/{max_retries}). Retrying in 2s...")
                        await asyncio.sleep(2 * (attempt + 1))
                        continue

                    resp.raise_for_status()
                    data = resp.json()
                    choice_msg = data.get("choices", [{}])[0].get("message", {})
                    reply = choice_msg.get("content") or choice_msg.get("reasoning_details") or choice_msg.get("reasoning") or ""
                    tokens = data.get("usage", {}).get("total_tokens", len(reply.split()))
                    return reply, tokens
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 429:
                        last_error = exc.response.text
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    raise LLMError(f"OpenRouter API error {exc.response.status_code}: {exc.response.text[:200]}") from exc
                except httpx.RequestError as exc:
                    raise LLMError(f"OpenRouter request failed: {exc}") from exc

        # If all retries exhausted on 429
        raise LLMError(f"OpenRouter upstream rate limit exceeded (model: {self._model}): {last_error[:200]}")


# ── Factory ───────────────────────────────────────────────────────────────────

def get_llm_client(settings: Settings) -> BaseLLMClient:
    provider = settings.llm_provider.lower()
    if provider in ("openrouter", "qwen"):
        return OpenRouterClient(settings)
    if provider in ("openai", "local"):
        return OpenAIClient(settings)
    if provider == "ollama":
        return OllamaClient(settings)
    return MockLLMClient()


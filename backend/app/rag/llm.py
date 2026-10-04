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


# ── Factory ───────────────────────────────────────────────────────────────────

def get_llm_client(settings: Settings) -> BaseLLMClient:
    provider = settings.llm_provider.lower()
    if provider == "openai" or provider == "local":
        return OpenAIClient(settings)
    if provider == "ollama":
        return OllamaClient(settings)
    return MockLLMClient()

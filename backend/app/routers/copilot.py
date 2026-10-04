"""AI Copilot / RAG chat endpoints."""
from __future__ import annotations

from datetime import datetime, timezone
import aiomysql
from fastapi import APIRouter, Depends, Query

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.db import acquire, execute, fetch_many
from app.db import queries as Q
from app.models import ChatMessageIn, ChatMessageOut, ChatResponse
from app.rag import BaseLLMClient, build_prompt, retrieve_context
from app.routers.deps import get_db_pool, get_llm

logger = get_logger(__name__)
router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/chat", response_model=ChatResponse)
async def chat_copilot(
    payload: ChatMessageIn,
    pool: aiomysql.Pool = Depends(get_db_pool),
    settings: Settings = Depends(get_settings),
    llm: BaseLLMClient = Depends(get_llm),
) -> ChatResponse:
    """
    Interact with NetOps Copilot.
    Retrieves live topology, telemetry, and alerts from MySQL, constructs
    the grounded RAG prompt, calls the LLM provider, and logs the exchange.
    """
    user_tokens = len(payload.content.split())
    now = datetime.now(timezone.utc)

    # 1. Save user query & retrieve RAG context
    async with acquire(pool) as conn:
        await execute(
            conn,
            Q.CHAT_INSERT,
            (payload.session_id, "user", payload.content, user_tokens),
        )

    context = await retrieve_context(
        pool,
        settings,
        device_id=payload.device_id,
        interface_id=payload.interface_id,
    )

    # 2. Build prompt from retrieved context
    messages = build_prompt(settings.prompt_version, context, payload.content)

    # 3. Call LLM (mock, openai, or ollama)
    reply_text, reply_tokens = await llm.complete(messages)

    # 4. Save assistant response
    async with acquire(pool) as conn:
        msg_id = await execute(
            conn,
            Q.CHAT_INSERT,
            (payload.session_id, "assistant", reply_text, reply_tokens),
        )

    assistant_msg = ChatMessageOut(
        id=msg_id,
        session_id=payload.session_id,
        role="assistant",
        content=reply_text,
        token_count=reply_tokens,
        created_at=now,
    )

    return ChatResponse(
        assistant_message=assistant_msg,
        context_metrics_used=len(context.metrics),
        context_alerts_used=len(context.alerts),
    )


@router.get("/history/{session_id}", response_model=list[ChatMessageOut])
async def get_chat_history(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    pool: aiomysql.Pool = Depends(get_db_pool),
) -> list[ChatMessageOut]:
    """Retrieve chat history for a given session."""
    async with acquire(pool) as conn:
        rows = await fetch_many(conn, Q.CHAT_HISTORY, (session_id, limit))

    return [ChatMessageOut(**r) for r in rows]

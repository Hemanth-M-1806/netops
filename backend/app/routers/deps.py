"""Router dependencies."""
from __future__ import annotations

import aiomysql
from fastapi import Depends, Request

from app.config import Settings, get_settings
from app.rag import BaseLLMClient, get_llm_client


def get_db_pool(request: Request) -> aiomysql.Pool:
    """Retrieve the global aiomysql pool from app.state."""
    return request.app.state.pool


def get_llm(settings: Settings = Depends(get_settings)) -> BaseLLMClient:
    """Provide configured LLM client instance."""
    return get_llm_client(settings)

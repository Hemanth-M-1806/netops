"""
Low-level DB helpers for raw aiomysql queries.

All functions accept an open aiomysql.Connection (not a pool).
Callers are responsible for acquiring / releasing via `async with pool.acquire()`.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import aiomysql
from app.core.errors import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def acquire(pool: aiomysql.Pool) -> AsyncGenerator[aiomysql.Connection, None]:
    """Context manager: borrow a connection from the pool."""
    try:
        async with pool.acquire() as conn:
            yield conn
    except aiomysql.Error as exc:
        logger.error("db.acquire.failed", extra={"error": str(exc)})
        raise DatabaseError(f"DB connection failed: {exc}") from exc


async def fetch_one(
    conn: aiomysql.Connection,
    sql: str,
    args: tuple | dict | None = None,
) -> dict[str, Any] | None:
    """Execute *sql* and return the first row as a dict, or None."""
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchone()
    except aiomysql.Error as exc:
        logger.error("db.fetch_one.error", extra={"sql": sql[:120], "error": str(exc)})
        raise DatabaseError(str(exc)) from exc


async def fetch_many(
    conn: aiomysql.Connection,
    sql: str,
    args: tuple | dict | None = None,
) -> list[dict[str, Any]]:
    """Execute *sql* and return all rows as a list of dicts."""
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(sql, args)
            return await cur.fetchall() or []
    except aiomysql.Error as exc:
        logger.error("db.fetch_many.error", extra={"sql": sql[:120], "error": str(exc)})
        raise DatabaseError(str(exc)) from exc


async def execute(
    conn: aiomysql.Connection,
    sql: str,
    args: tuple | dict | None = None,
) -> int:
    """Execute a write statement.  Returns lastrowid (INSERT) or rowcount."""
    try:
        async with conn.cursor() as cur:
            await cur.execute(sql, args)
            return cur.lastrowid or cur.rowcount
    except aiomysql.Error as exc:
        logger.error("db.execute.error", extra={"sql": sql[:120], "error": str(exc)})
        raise DatabaseError(str(exc)) from exc


async def executemany(
    conn: aiomysql.Connection,
    sql: str,
    args_list: list[tuple | dict],
) -> int:
    """Bulk-insert helper.  Returns rowcount."""
    if not args_list:
        return 0
    try:
        async with conn.cursor() as cur:
            await cur.executemany(sql, args_list)
            return cur.rowcount
    except aiomysql.Error as exc:
        logger.error("db.executemany.error", extra={"sql": sql[:120], "error": str(exc)})
        raise DatabaseError(str(exc)) from exc

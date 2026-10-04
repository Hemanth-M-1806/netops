"""
Raw aiomysql connection pool.

Usage:
    pool = await create_pool(settings)        # call once in lifespan
    async with acquire(pool) as conn:
        rows = await fetch_many(conn, SQL, args)
    await pool.close()
"""
from __future__ import annotations

import aiomysql
from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def create_pool(settings: Settings) -> aiomysql.Pool:
    """Create the global connection pool.  Call once at startup."""
    pool = await aiomysql.create_pool(
        minsize=2,
        maxsize=settings.db_pool_size + settings.db_max_overflow,
        **settings.db_dsn,
    )
    logger.info(
        "db.pool.created",
        extra={
            "host": settings.mysql_host,
            "port": settings.mysql_port,
            "db": settings.mysql_database,
        },
    )
    return pool

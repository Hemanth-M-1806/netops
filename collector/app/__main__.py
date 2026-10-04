"""Entrypoint: `python -m app` or `uvicorn app.main:app`."""

from __future__ import annotations

import uvicorn

from app.config import get_settings
from app.main import create_app

if __name__ == "__main__":
    settings = get_settings()
    app = create_app(settings)
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_config=None,  # We configure logging ourselves.
        access_log=False,
    )

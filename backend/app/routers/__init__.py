"""app/routers package."""
from app.routers.alerts import router as alerts_router
from app.routers.copilot import router as copilot_router
from app.routers.devices import router as devices_router
from app.routers.health import router as health_router
from app.routers.interfaces import router as interfaces_router
from app.routers.telemetry import router as telemetry_router

__all__ = [
    "devices_router",
    "interfaces_router",
    "telemetry_router",
    "alerts_router",
    "copilot_router",
    "health_router",
]

"""Runner: wires topology + scenario/generator + sink into a Simulator.

Separated from the CLI so it can be called programmatically (tests, docker
entrypoint) without argparse.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.domain.models import InterfaceState
from app.engine.simulator import Simulator
from app.generators import build_generator
from app.scenarios import Scenario, build_scenario
from app.sinks import ApiSink, LogSink
from app.topology import TopologyResolver, default_topology

logger = get_logger(__name__)


@dataclass(slots=True)
class RunConfig:
    """User-facing run options (populated by the CLI)."""

    scenario_name: str | None = None
    generator_name: str | None = None
    ticks: int | None = None
    duration_seconds: float | None = None
    dry_run: bool = False
    verbose: bool = False
    interval_seconds: float | None = None
    seed: int | None = None


def _resolve_scenario(config: RunConfig, settings: Settings) -> Scenario:
    """Build the scenario from either ``--scenario`` or ``--generator``."""
    if config.generator_name:
        generator = build_generator(config.generator_name)
        return Scenario(
            name=f"single:{generator.name}",
            description=f"Isolated run of the '{generator.name}' generator.",
            default_generator=generator,
        )
    name = config.scenario_name or settings.default_scenario
    return build_scenario(name)


async def run(config: RunConfig, settings: Settings | None = None) -> dict:
    """Execute a simulation run and return the engine summary."""
    settings = settings or get_settings()

    # CLI overrides take precedence over environment values.
    updates: dict[str, object] = {}
    if config.interval_seconds is not None:
        updates["interval_seconds"] = config.interval_seconds
    if config.seed is not None:
        updates["random_seed"] = config.seed
    if updates:
        settings = settings.model_copy(update=updates)

    dry_run = config.dry_run or settings.dry_run
    scenario = _resolve_scenario(config, settings)

    backend_client = None
    collector_client = None
    if dry_run:
        sink = LogSink(verbose=config.verbose)
        directory = None
    else:
        from app.client import BackendClient, CollectorClient  # light for dry-run

        # Discovery (devices/interfaces) comes from the backend.
        backend_client = BackendClient(settings)
        # Telemetry goes to the collection layer, which forwards it to the backend.
        collector_client = CollectorClient(settings)
        sink = ApiSink(collector_client, batch_size=settings.batch_size)
        directory = backend_client

    resolver = TopologyResolver(
        directory, allow_synthetic=settings.allow_synthetic_topology
    )

    async def _close_clients() -> None:
        for client in (backend_client, collector_client):
            if client is not None:
                await client.close()

    interfaces: list[InterfaceState]
    try:
        interfaces = await resolver.resolve(default_topology())
    except Exception:
        await _close_clients()
        raise

    logger.info(
        "run.start",
        extra={"scenario": scenario.name, "stage": "runner"},
    )

    simulator = Simulator(
        settings=settings,
        interfaces=interfaces,
        sink=sink,
        generator_for=scenario.generator_for,
        reset_generators=scenario.reset,
    )

    try:
        summary = await simulator.run(
            ticks=config.ticks, duration_seconds=config.duration_seconds
        )
    finally:
        await sink.close()
        await _close_clients()

    summary["scenario"] = scenario.name
    summary["interfaces"] = len(interfaces)
    summary["dry_run"] = dry_run
    return summary

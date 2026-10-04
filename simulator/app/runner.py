"""Runner: wires topology + scenario/generator + sink into a Simulator.

Separated from the CLI so it can be called programmatically (tests, docker
entrypoint) without argparse.
"""

from __future__ import annotations

from dataclasses import dataclass

from app import status as status_server
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

    # Mutable holder so the status dashboard can hot-swap scenarios mid-run
    # (fault injection buttons on http://localhost:8200).
    active_scenario: dict = {"scenario": scenario}
    status_server.set_scenario_holder(active_scenario)

    # Start the browsable status endpoint early so it also covers discovery.
    status_server.start(settings, scenario.name)

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
        status_server.stop()
        await _close_clients()
        raise

    logger.info(
        "run.start",
        extra={"scenario": scenario.name, "stage": "runner"},
    )

    async def _report_statuses(
        device_status: dict[str, str], interface_status: dict[int, str]
    ) -> None:
        """Push changed statuses to the backend so outages show on the dashboard."""
        if backend_client is None:
            return  # dry-run has no directory to report to
        try:
            if device_status:
                await backend_client.update_device_statuses(
                    [{"hostname": h, "status": s} for h, s in device_status.items()]
                )
            if interface_status:
                await backend_client.update_interface_statuses(
                    [{"interface_id": i, "status": s} for i, s in interface_status.items()]
                )
        except Exception as exc:
            # Status reporting must never kill the simulation loop.
            logger.warning(
                "status.report_failed",
                extra={"stage": "runner", "error": str(exc)},
            )

    simulator = Simulator(
        settings=settings,
        interfaces=interfaces,
        sink=sink,
        generator_for=lambda state: active_scenario["scenario"].generator_for(state),
        reset_generators=lambda: active_scenario["scenario"].reset(),
        status_sink=_report_statuses,
    )
    status_server.set_simulator(simulator)

    try:
        summary = await simulator.run(
            ticks=config.ticks, duration_seconds=config.duration_seconds
        )
    finally:
        status_server.stop()
        await sink.close()
        await _close_clients()

    summary["scenario"] = scenario.name
    summary["interfaces"] = len(interfaces)
    summary["dry_run"] = dry_run
    return summary

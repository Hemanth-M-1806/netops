"""The simulation engine: turns generators + topology + a sink into a loop."""

from __future__ import annotations

import random
from datetime import datetime

from app.config import Settings
from app.core.errors import GenerationError
from app.core.logging import get_logger
from app.domain.models import InterfaceState, MetricPayload
from app.engine.clock import Clock, SystemClock
from app.generators.base import GeneratorContext
from app.sinks.base import Sink

logger = get_logger(__name__)


class Simulator:
    """Orchestrates generation for a set of resolved interfaces."""

    def __init__(
        self,
        *,
        settings: Settings,
        interfaces: list[InterfaceState],
        sink: Sink,
        generator_for,  # Callable[[InterfaceState], TrafficGenerator]
        reset_generators=None,
        clock: Clock | None = None,
        rng: random.Random | None = None,
    ) -> None:
        self._settings = settings
        self._interfaces = interfaces
        self._sink = sink
        self._generator_for = generator_for
        self._reset_generators = reset_generators or (lambda: None)
        self._clock = clock or SystemClock()
        self._rng = rng or random.Random(settings.random_seed)

        self.tick_index = 0
        self.totals: dict[str, int] = {
            "ticks": 0,
            "samples": 0,
            "accepted": 0,
            "failures": 0,
        }

    # ------------------------------------------------------------------ #
    # One iteration
    # ------------------------------------------------------------------ #
    async def tick(self) -> dict:
        """Generate one interval for every interface and deliver the batch."""
        now = self._clock.now()
        ctx = GeneratorContext(
            rng=self._rng,
            now=now,
            interval_seconds=self._settings.interval_seconds,
            config=self._settings,
        )

        payloads: list[MetricPayload] = []
        device_status: dict[str, str] = {}

        for state in self._interfaces:
            generator = self._generator_for(state)
            try:
                result = generator.sample(state, ctx)
            except Exception as exc:  # keep one bad generator from killing the loop
                self.totals["failures"] += 1
                logger.error(
                    "tick.generator_failed",
                    extra={"generator": generator.name, "interface": state.name},
                    exc_info=True,
                )
                # Surface a typed error for callers that want to fail fast.
                _ = GenerationError(generator.name, str(exc))
                continue

            state.tick += 1
            if result.interface_status is not None:
                state.status = result.interface_status
            state.rx_bytes = result.sample.rx_bytes
            state.tx_bytes = result.sample.tx_bytes
            state.packet_drops = result.sample.packet_drops
            state.errors = result.sample.errors

            payloads.append(
                MetricPayload(
                    interface_id=state.interface_id,
                    rx_bytes=result.sample.rx_bytes,
                    tx_bytes=result.sample.tx_bytes,
                    packet_drops=result.sample.packet_drops,
                    errors=result.sample.errors,
                    measured_at=now,
                )
            )

            if result.device_status is not None:
                device_status[state.device_hostname] = result.device_status

        delivered = await self._sink.send(payloads)

        self.tick_index += 1
        self.totals["ticks"] += 1
        self.totals["samples"] += len(payloads)
        self.totals["accepted"] += int(delivered.get("accepted", len(payloads)))

        return {
            "tick": self.tick_index,
            "samples": len(payloads),
            "accepted": int(delivered.get("accepted", len(payloads))),
            "device_status": device_status,
        }

    # ------------------------------------------------------------------ #
    # The loop
    # ------------------------------------------------------------------ #
    async def run(
        self,
        *,
        ticks: int | None = None,
        duration_seconds: float | None = None,
    ) -> dict:
        """Run ``ticks`` iterations (or until ``duration_seconds`` elapses).

        With both ``None`` the loop runs until cancelled (Ctrl+C).
        """
        self._reset_generators()
        start: datetime = self._clock.now()
        index = 0

        try:
            while not self._should_stop(index, start, ticks, duration_seconds):
                summary = await self.tick()
                index += 1
                logger.info(
                    "tick.complete",
                    extra={"tick": summary["tick"]},
                )
                if not self._should_stop(index, start, ticks, duration_seconds):
                    await self._clock.sleep(self._settings.interval_seconds)
        except (KeyboardInterrupt, Exception) as exc:  # noqa: BLE001 - report and stop
            if isinstance(exc, KeyboardInterrupt):
                logger.info("run.interrupted", extra={"stage": "engine"})
            else:
                logger.error("run.failed", extra={"stage": "engine"}, exc_info=True)
                raise

        return {"totals": dict(self.totals), "ticks": index}

    # ------------------------------------------------------------------ #
    def _should_stop(
        self,
        index: int,
        start: datetime,
        ticks: int | None,
        duration_seconds: float | None,
    ) -> bool:
        if ticks is not None and index >= ticks:
            return True
        if duration_seconds is not None:
            elapsed = (self._clock.now() - start).total_seconds()
            if elapsed >= duration_seconds:
                return True
        return False

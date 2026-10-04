"""Command line interface for the simulator.

Examples
--------
List what is available::

    python -m app --list-scenarios
    python -m app --list-generators

Debug a single generator offline (no backend needed)::

    python -m app --generator packet_drops --dry-run --ticks 5 --verbose

Run a full scenario against the backend::

    python -m app --scenario mixed --interval 5
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.config import get_settings
from app.core.errors import SimulatorError
from app.core.logging import configure_logging
from app.generators import GENERATOR_REGISTRY
from app.runner import RunConfig, run
from app.scenarios import list_scenarios


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="simulator",
        description="Router telemetry simulator (dev-only microservice).",
    )
    parser.add_argument("--scenario", help="Scenario to run (default: from settings).")
    parser.add_argument(
        "--generator",
        help="Run a single generator in isolation (debugging).",
    )
    parser.add_argument("--ticks", type=int, default=None, help="Number of ticks to run.")
    parser.add_argument(
        "--duration", type=float, default=None, help="Run for N seconds instead of ticks."
    )
    parser.add_argument(
        "--interval", type=float, default=None, help="Seconds between ticks."
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and log only; do not POST to the backend.",
    )
    parser.add_argument("--verbose", action="store_true", help="Log every sample.")
    parser.add_argument("--json-logs", action="store_true", help="Emit JSON log lines.")
    parser.add_argument(
        "--list-scenarios", action="store_true", help="List scenarios and exit."
    )
    parser.add_argument(
        "--list-generators", action="store_true", help="List generators and exit."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = get_settings()
    configure_logging(settings.log_level, json_logs=args.json_logs)

    # ---- info-only modes --------------------------------------------------
    if args.list_scenarios:
        print("Scenarios:")
        for name in list_scenarios():
            print(f"  - {name}")
        return 0

    if args.list_generators:
        print("Generators:")
        for name, cls in sorted(GENERATOR_REGISTRY.items()):
            print(f"  - {name:<18} {cls.description}")
        return 0

    # ---- validation -------------------------------------------------------
    if args.scenario and args.generator:
        parser.error("choose either --scenario or --generator, not both")

    config = RunConfig(
        scenario_name=args.scenario,
        generator_name=args.generator,
        ticks=args.ticks,
        duration_seconds=args.duration,
        dry_run=args.dry_run,
        verbose=args.verbose,
        interval_seconds=args.interval,
        seed=args.seed,
    )

    try:
        summary = asyncio.run(run(config, settings))
    except SimulatorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:  # pragma: no cover - interactive
        print("stopped", file=sys.stderr)
        return 130

    print(
        f"done: scenario={summary['scenario']} "
        f"interfaces={summary['interfaces']} "
        f"ticks={summary['totals']['ticks']} "
        f"samples={summary['totals']['samples']} "
        f"accepted={summary['totals']['accepted']} "
        f"failures={summary['totals']['failures']} "
        f"dry_run={summary['dry_run']}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

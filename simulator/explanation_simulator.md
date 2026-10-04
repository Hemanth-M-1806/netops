# `simulator/` — Complete Code Explanation

> **Audience:** A developer who has never seen this project.  
> **Goal:** After reading this document, you should understand *every file*, *why it exists*, and *how to safely change or extend it*.  
>
> The simulator is a **standalone microservice**. It fakes network routers, switches, firewalls, and access points so the NOC dashboard shows live, believable telemetry without requiring physical hardware.  
> It never connects directly to the database — it queries the backend API for device topology discovery, and pushes telemetry samples into the **collection layer** (`collector/`).

---

## 0. The One-Paragraph Summary

A **generator** produces one interval of telemetry (bytes, packets, drops, errors) for one interface.  
A **scenario** decides which generator runs on which interface.  
The **engine** loops over every interface, collects the generated samples, and hands them to a **sink** — either the live collection layer (`ApiSink` backed by `CollectorClient`) or the terminal logs (`LogSink`, used for `--dry-run`).  
The **resolver** turns the blueprint's human-readable names (`R1` / `Gi0/1`) into real `interface_id` foreign keys by querying the backend's directory endpoint (`BackendClient`).

---

## 1. How the Pieces Fit Together

```
                     ┌──────────────────────── app/cli.py ───────────────────────┐
   you type ────────►│ parse flags → build RunConfig → asyncio.run(runner.run)   │
                     └───────────────────────────┬──────────────────────────────┘
                                                 ▼
                                        app/runner.py  (the "wiring")
                          ┌──────────────────────┼───────────────────────┐
                          ▼                      ▼                       ▼
                   app/topology/           app/scenarios/            app/sinks/
            blueprint + resolver        pick generators        ApiSink  |  LogSink
                  │          │                   │                 │         │
    queries       ▼          │                   │                 ▼         │
  BackendClient ──┘          └──────────► app/engine/Simulator ◄─── CollectorClient
  (:8000 discovery)                              │  (the loop)     (:8100 ingest)
                                                 ▼
                                      app/generators/  (one file per behaviour)
                                                 │
                                                 ▼
                                        app/domain/  (data structures)

   app/config.py  ── settings used everywhere (SIMULATOR_* env vars)
   app/core/      ── logging + typed errors used everywhere
   app/client/    ── BackendClient (discovery) + CollectorClient (ingestion) + retry
```

---

## 2. What Happens During *One Tick* (The Core Idea)

"A tick" = one sampling interval (default 5 seconds of *simulated* time).

1. `Simulator.tick()` asks the clock for the current time.
2. It builds a `GeneratorContext` (shared random number generator, current timestamp, interval, settings).
3. For **each** interface in the resolved topology:
   a. Ask the scenario: *"Which generator owns this interface?"*
   b. Call `generator.sample(state, context)` $\rightarrow$ returns a `GeneratorResult`.
   c. Copy the counters onto the live `InterfaceState` (so stateful generators can build on the previous tick) and append a `MetricPayload`.
4. Hand the complete list of payloads to the sink (`await sink.send(payloads)`).
   - In live mode (`ApiSink`), this pushes the batch to the **collection layer** (`POST http://localhost:8100/ingest`).
   - In dry-run mode (`LogSink`), this formats and logs the metrics locally without any network I/O.
5. Update counters (`ticks`, `samples`, `accepted`, `failures`).

This loop repeats until `--ticks` is reached, `--duration` elapses, or you press `Ctrl+C`.

---

## 3. Root-Level Files (`simulator/`)

### `requirements.txt`
The **runtime** dependencies — packages required to run the service in production or Docker:
- `pydantic >= 2.8.0` & `pydantic-settings >= 2.4.0`: Strict type validation and environment variable parsing.
- `httpx >= 0.27.0`: Production async HTTP client for backend discovery and collector ingestion.
- `python-dotenv >= 1.0.0`: Automatically reads `.env` files.

### `requirements-dev.txt`
Extra dependencies for testing and development:
- `-r requirements.txt`: Includes all runtime dependencies.
- `pytest >= 8.3.0`, `pytest-asyncio >= 0.24.0`, `anyio >= 4.4.0`: Test runner and asynchronous test execution.

### `pytest.ini`
Configures pytest execution:
```ini
[pytest]
asyncio_mode = auto
pythonpath = .
testpaths = tests
```

### `.env.example`
A template listing all `SIMULATOR_*` variables with defaults. Copy to `.env` or set in the environment:
- `SIMULATOR_API_BASE_URL=http://localhost:8000/api/v1`
- `SIMULATOR_COLLECTOR_URL=http://localhost:8100/ingest`
- `SIMULATOR_INTERVAL_SECONDS=5.0`
- `SIMULATOR_DEFAULT_SCENARIO=mixed`

### `Dockerfile`
Containerizes the simulator using `python:3.12-slim`. It installs `requirements.txt` first for optimal Docker layer caching, then copies `app/`. The default `CMD` runs `python -m app --scenario mixed`.

### `README.md`
Quick-start documentation covering CLI flags, scenario descriptions, and ingestion architecture.

### `explanation_simulator.md`
This document.

---

## 4. The `app/` Package

### `app/__init__.py`
Defines package metadata and version: `__version__ = "0.1.0"`.

### `app/__main__.py`
The package entry point allowing `python -m app` execution. It delegates immediately to `app.cli.main()`.

### `app/config.py`
All simulator tunables live here. `Settings` is a `pydantic-settings` class reading environment variables with the `SIMULATOR_` prefix:

| Field | Env Var | Default | Meaning |
|---|---|---|---|
| `api_base_url` | `SIMULATOR_API_BASE_URL` | `http://localhost:8000/api/v1` | Backend root for device/interface discovery |
| `collector_url` | `SIMULATOR_COLLECTOR_URL` | `http://localhost:8100/ingest` | Collection layer ingest endpoint for telemetry |
| `timeout_seconds` | `SIMULATOR_TIMEOUT_SECONDS` | `10.0` | HTTP request timeout |
| `max_retries` | `SIMULATOR_MAX_RETRIES` | `3` | Retries for transient network transport errors |
| `retry_backoff_seconds` | `SIMULATOR_RETRY_BACKOFF_SECONDS` | `0.5` | Exponential backoff multiplier |
| `batch_size` | `SIMULATOR_BATCH_SIZE` | `200` | Max samples sent per HTTP POST |
| `interval_seconds` | `SIMULATOR_INTERVAL_SECONDS` | `5.0` | Seconds of simulated time per tick |
| `random_seed` | `SIMULATOR_RANDOM_SEED` | `None` | Integer seed for deterministic, repeatable runs |
| `default_scenario` | `SIMULATOR_DEFAULT_SCENARIO` | `mixed` | Scenario invoked when `--scenario` is omitted |
| `dry_run` | `SIMULATOR_DRY_RUN` | `False` | When True, logs metrics instead of POSTing |
| `log_level` | `SIMULATOR_LOG_LEVEL` | `INFO` | Logger verbosity |
| `allow_synthetic_topology` | `SIMULATOR_ALLOW_SYNTHETIC_TOPOLOGY` | `True` | Fallback synthetic IDs if backend is unseeded |

### `app/cli.py`
Command-line argument parser built with `argparse`. Handles:
- Selecting scenarios (`--scenario <name>`) or isolating single generators (`--generator <name>`).
- Duration control (`--ticks <N>`, `--duration <seconds>`, `--interval <seconds>`).
- Offline modes (`--dry-run`, `--verbose`, `--json-logs`).
- Catalog introspection (`--list-scenarios`, `--list-generators`).
- Graceful shutdown handling (`Ctrl+C` catches `KeyboardInterrupt` and exits with code 130).

### `app/runner.py`
The orchestration wiring layer:
- `RunConfig`: Dataclass holding CLI flags.
- `_resolve_scenario()`: Maps `--generator` to an isolated single-rule scenario or constructs named scenarios from the catalog.
- `run()`:
  1. Instantiates `BackendClient` pointing to `:8000` (for topology discovery).
  2. In live mode, instantiates `CollectorClient` pointing to `:8100` and wraps it in `ApiSink`. In dry-run mode, instantiates `LogSink`.
  3. Resolves network blueprint names to real `interface_id`s via `TopologyResolver`.
  4. Runs `Simulator.run()`.
  5. Cleanly closes both HTTP clients in a `finally` block.

---

## 5. `app/core/` — Cross-Cutting Building Blocks

### `app/core/logging.py`
Structured logging shared across the service:
- `JsonFormatter`: Outputs one JSON object per line with timestamp, module, level, message, and contextual metadata (`stage`, `scenario`, `generator`, `tick`).
- `TextFormatter`: Terminal-friendly colored logs.
- `configure_logging(level, json_logs=False)`: Initializes root logging and suppresses noisy third-party loggers.
- `get_logger(name)`: Module logger factory.

### `app/core/errors.py`
Typed exception hierarchy:
- `SimulatorError`: Base exception with `stage` tagging.
- `ConfigurationError`: Bad parameters or invalid generator/scenario names.
- `TopologyError`: Failure resolving device or interface IDs.
- `GenerationError`: Failure inside a generator's `sample()` method.
- `IngestError`: Failure communicating with backend or collection layer.
- `ScenarioError`: Invalid scenario configuration.

---

## 6. `app/domain/` — Data Structures

Pure data classes and enums with zero network I/O:

### `app/domain/enums.py`
String enums mirroring MySQL schema check constraints:
- `DeviceType`: `router`, `switch`, `firewall`, `loadbalancer`, `access_point`, `other`.
- `DeviceStatus`: `UP`, `DOWN`, `WARNING`, `CRITICAL`, `MAINTENANCE`, `UNKNOWN`.
- `InterfaceType`: `ethernet`, `loopback`, `vlan`, `tunnel`.
- `InterfaceStatus`: `UP`, `DOWN`, `ADMIN_DOWN`, `ERROR`, `UNKNOWN`.
- `Severity`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.

### `app/domain/models.py`
Dataclasses with `slots=True`:
- `InterfaceSpec` & `DeviceSpec`: Static blueprints defining device hostnames, interface names, speed capacity, and baseline utilization.
- `InterfaceState`: Mutable live state tracked across ticks: ID, capacity, baseline, current status, previous sample, and `health` factor ($1.0 = \text{healthy} \rightarrow 0.0 = \text{down}$).
- `InterfaceSample`: Quadruple of measurements: `rx_bytes`, `tx_bytes`, `packet_drops`, `errors`.
- `GeneratorResult`: Value returned by a generator's `sample()` method, containing an `InterfaceSample` and optional status overrides.
- `MetricPayload`: Wire format representation. `as_ingest_body()` formats samples into the ISO timestamped dictionary expected by collection and backend layers.

---

## 7. `app/generators/` — Traffic Behaviours

Each generator models a distinct networking condition in its own isolated file:

### `app/generators/base.py`
- `TrafficGenerator(ABC)`: Base class requiring `sample(state, ctx) -> GeneratorResult` and optional `reset()`.
- `GeneratorContext`: Frozen execution context containing shared `random.Random`, clock `now`, `interval_seconds`, and `Settings`.
- Helper functions: `clamp(val, low, high)`, `max_bytes_per_interval(capacity, interval)`, `jitter(rng, base, spread)`.

### Generator Implementations:
1. **`normal.py` (`NormalGenerator`):**  
   Steady-state traffic centered around baseline link utilization with light random noise. Drops and errors remain zero. Health drifts toward 1.0.
2. **`high_traffic.py` (`HighTrafficGenerator`):**  
   Heavy utilization (70–90%) representing legitimate high-bandwidth transfers without packet loss.
3. **`packet_drops.py` (`PacketDropGenerator`):**  
   Progressive buffer exhaustion and congestion. As link health degrades, utilization rises and packet drops scale super-linearly ($1 + 25 \times \text{severity}$).
4. **`errors.py` (`ErrorGenerator`):**  
   Physical link degradation (faulty SFP transceiver or damaged fiber). Transmits normal byte volumes, but framing and CRC error counts climb. Sets interface status to `ERROR` when severity exceeds 0.5.
5. **`spikes.py` (`SpikeGenerator`):**  
   Bursty behavior. Mostly normal traffic interrupted periodically by sudden utilization spikes.
6. **`failures.py`:**  
   - `InterfaceFailureGenerator`: Flaps an interface `DOWN` with configurable probabilities. Emits zero traffic while down.
   - `DeviceFailureGenerator`: Simulates a complete device outage. Once triggered, all interfaces on the affected device report `DOWN` and emit zero traffic simultaneously.

### `app/generators/__init__.py`
Central registry `GENERATOR_REGISTRY` mapping names to generator classes, plus `build_generator(name, **params)`.

---

## 8. `app/scenarios/` — Composing Multi-Device Scenarios

### `app/scenarios/base.py`
- `on(hostname, interface_name=None)`: Predicate matcher targeting specific devices or interfaces.
- `ScenarioRule`: Pairs a generator with a matcher.
- `Scenario`: Holds a default generator and a list of rules. `generator_for(state)` evaluates rules sequentially, returning the first match or falling back to the default.

### `app/scenarios/catalog.py`
Registers 8 standard scenarios:
- `normal`, `high_traffic`, `packet_drops`, `errors`, `spikes`, `interface_failure`, `device_failure`.
- **`mixed` (Default):** Simulates a realistic active network:
  - `R1 Gi0/1` experiences packet drops.
  - `CORE-SW1 Gi1/0/2` experiences CRC errors.
  - `R2 Gi0/0` experiences traffic spikes.
  - `FW1 eth0` experiences high throughput.
  - `AP1 eth0` flaps down and up.
  - All other links run normal steady-state traffic.

### `app/scenarios/registry.py` & `app/scenarios/__init__.py`
`build_scenario(name)` and `list_scenarios()`.

---

## 9. `app/topology/` — Blueprint & Resolver

### `app/topology/blueprint.py`
`default_topology()` defines the demo network blueprint:
- Core routers: `R1` (10.0.0.1) and `R2` (10.0.0.2) with 10 Gbps uplinks and loopbacks.
- Distribution switches: `CORE-SW1` (10.0.0.10) and `CORE-SW2` (10.0.0.11) with 1 Gbps access ports and VLANs.
- Edge firewall: `FW1` (10.0.0.20) with WAN and LAN interfaces.
- Wireless access point: `AP1` (10.0.0.30) with Ethernet uplink and 2.4GHz / 5GHz radios.

### `app/topology/resolver.py`
Maps blueprint device and interface names to database primary keys:
- `DeviceDirectory` Protocol: Requires `list_devices()` and `list_interfaces(device_id)`.
- `TopologyResolver.resolve(blueprint)` queries the directory to find real IDs. If the backend is empty or unreachable and `allow_synthetic` is enabled, it generates deterministic synthetic IDs so tests and offline dry-runs work seamlessly.

---

## 10. `app/sinks/` — Telemetry Destinations

### `app/sinks/base.py`
Defines the `Sink` protocol:
```python
class Sink(Protocol):
    async def send(self, payloads: list[MetricPayload]) -> dict: ...
    async def close(self) -> None: ...
```

### `app/sinks/api_sink.py`
Live telemetry sink. Wraps a `TelemetryClient` (implemented by `CollectorClient`):
- Splices metric payloads into batches based on `batch_size`.
- Executes `await client.ingest(batch)`.
- Returns total accepted sample counts.

### `app/sinks/log_sink.py`
Zero-I/O dry-run sink. Logs metrics directly to console output without network communication.

---

## 11. `app/client/` — Downstream Communication & Resilience

### `app/client/envelope.py`
Provides `unwrap(body: dict) -> Any`:
Extracts the `data` field from standard `{ "success": true, "data": ... }` API responses. If `success` is False, raises a typed `IngestError`.

### `app/client/retry.py`
`call_with_retry(coroutine_factory, attempts, backoff_seconds)`:
Executes an async operation with exponential backoff on transport errors (`httpx.TransportError`, `httpx.TimeoutException`).

### `app/client/backend_client.py`
Async HTTP client for **device discovery** against `http://localhost:8000/api/v1`:
- `list_devices()` $\rightarrow$ `GET /devices`
- `list_interfaces(device_id)` $\rightarrow$ `GET /devices/{id}/interfaces`
Implements the `DeviceDirectory` protocol used by `TopologyResolver`.

### `app/client/collector_client.py`
Async HTTP client for **telemetry submission** against `http://localhost:8100/ingest`:
- `ingest(payloads)`: Formats payloads into `{"source": "simulator", "samples": [...]}` and POSTs them to the collection layer.
- Retries on network glitches and converts HTTP failures into `IngestError`.

---

## 12. `app/engine/` — Simulation Engine Loop

### `app/engine/clock.py`
Controllable time abstractions:
- `Clock` (Protocol): `now()` and `async sleep(seconds)`.
- `SystemClock`: Uses real system time and `asyncio.sleep()`.
- `FrozenClock`: Controllable mock clock for instant, deterministic unit testing.

### `app/engine/simulator.py`
`Simulator` executes the tick loop:
- `tick()`: Generates samples for every interface, updates states, and sends payloads to the configured sink.
- `run(ticks, duration_seconds)`: Loops until tick or duration limits are reached. Generator exceptions are isolated and logged so an individual fault never crashes the entire simulation.

---

## 13. `app/utils/` — Chunking Utilities

### `app/utils/chunking.py`
`chunked(items, size)`: Generator yielding sliced lists of at most `size` items for batching HTTP transmissions.

---

## 14. `tests/` — Test Suite

Contains 52 tests covering all modules:
- `test_chunking.py`: Batch slicing boundaries.
- `test_client.py`: Envelope unwrapping, retry recovery, and retry exhaustion.
- `test_engine.py`: Engine tick execution, frozen clock duration, and error isolation.
- `test_generators.py`: Generator output ranges, link capacity limits, and packet drop escalation.
- `test_models.py`: Wire format serialization and interface down properties.
- `test_scenarios.py`: Scenario catalog instantiation and interface rule matching.
- `test_sinks.py`: `ApiSink` chunking and `LogSink` dry-run behavior.
- `test_topology.py`: Real ID resolution and synthetic ID fallbacks.

Run with:
```bash
cd simulator
.\.venv\Scripts\python.exe -m pytest tests -v
```

---

## 15. Operational Commands & CLI Examples

```powershell
# 1. Discover available components
python -m app --list-scenarios
python -m app --list-generators

# 2. Offline isolated generator testing (zero backend needed)
python -m app --generator packet_drops --dry-run --ticks 5 --verbose

# 3. Live simulation using default 'mixed' scenario (5s tick interval)
python -m app --scenario mixed --interval 5

# 4. Stress testing link saturation
python -m app --scenario high_traffic --duration 60 --interval 2
```

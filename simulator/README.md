# Telemetry Simulator (dev-only microservice)

Generates realistic router/interface telemetry and pushes it to the backend
ingestion endpoint. It exists so the dashboard shows live, believable data
without any physical routers.

It is a **standalone service**: it has its own package, its own dependencies and
its own tests. Every behaviour lives in its own module so a bug in one function
can be fixed and re-tested without touching anything else.

## Architecture

```
        CLI (app/cli.py)  ──parses flags──►  runner (app/runner.py)
                                                  │
                          ┌───────────────────────┼────────────────────────┐
                          ▼                       ▼                        ▼
                    topology/                scenarios/                 sinks/
              (blueprint + resolver)     (generators compose)      ApiSink | LogSink
                          │                       │                        │
                          └──────────► engine/Simulator ◄──────────────────┘
                                            │
                                     generators/  (one file per behaviour)
                                            │
                                      domain/ (models + enums)
```

## Module map (each is independently testable)

| Path | Responsibility |
|---|---|
| `app/config.py` | All tunables (`SIMULATOR_*` env vars) |
| `app/core/logging.py` | Structured logging (module name on every line) |
| `app/core/errors.py` | Typed errors carrying the failing `stage` |
| `app/domain/` | Enums (mirror DB CHECK constraints) + dataclasses |
| `app/topology/blueprint.py` | The demo network we simulate |
| `app/topology/resolver.py` | Maps blueprint names → real `interface_id`s |
| `app/generators/*.py` | One generator per behaviour |
| `app/scenarios/` | Compose generators into named scenarios |
| `app/sinks/` | `ApiSink` (live) or `LogSink` (dry-run) |
| `app/client/` | HTTP client + retry/backoff |
| `app/engine/` | Clock abstraction + the run loop |

## Generators

| Name | Behaviour |
|---|---|
| `normal` | Steady-state traffic around the baseline |
| `high_traffic` | High RX/TX utilisation, still healthy |
| `packet_drops` | Congestion with **escalating** packet drops |
| `errors` | Degrading link with rising error counters |
| `spikes` | Sudden bursts on a normal baseline |
| `interface_failure` | Interfaces flap `DOWN` / recover |
| `device_failure` | Whole device outage (all interfaces silent) |

## Scenarios

`normal`, `high_traffic`, `packet_drops`, `errors`, `spikes`,
`interface_failure`, `device_failure`, and **`mixed`** (the default — a healthy
network with a few targeted faults so anomalies stand out on the dashboard).

## Usage

```bash
# See what is available
python -m app --list-generators
python -m app --list-scenarios

# Debug ONE generator offline — no backend required
python -m app --generator packet_drops --dry-run --ticks 5 --verbose

# Run a full scenario against the backend
python -m app --scenario mixed --interval 5

# Time-boxed run
python -m app --scenario spikes --duration 60
```

### Debugging a single function

The `--dry-run` flag swaps `ApiSink` for `LogSink`, and `--generator` isolates
one behaviour. Combined with structured logs (which always include the module
name and the `stage`), a failure tells you exactly which file to open:

```
INFO  app.generators.packet_drops   :: ...      # works
ERROR app.generators.errors ...     exc_info=.. # traceback points here
```

## Ingestion contract

The simulator POSTs to `POST {SIMULATOR_API_BASE_URL}{SIMULATOR_INGEST_PATH}`:

```json
{ "samples": [
  { "interface_id": 12, "rx_bytes": 1234, "tx_bytes": 987,
    "packet_drops": 0, "errors": 0, "measured_at": "2024-01-01T12:00:00+00:00" }
] }
```

Values are **per-interval** amounts (bytes/drops/errors accumulated during one
sampling interval). The backend replies with the standard API envelope
(`{ "success": true, "data": { "accepted": N } }`), which the client unwraps.

## Extending

* **New behaviour** → add `app/generators/<name>.py` with a `TrafficGenerator`
  subclass, register it in `app/generators/__init__.py`.
* **New scenario** → add a factory in `app/scenarios/catalog.py`.

Nothing else changes — that is the point of the layout.

## Tests

```bash
python -m pytest            # 49 tests, one module per source module
```

# `collector/` — Telemetry Collection Layer: Complete Code Explanation

> **Audience:** A developer, SRE, or network engineer who has never seen this repository before.  
> **Goal:** After reading this document, you will understand *every file* in `collector/`, *why it was created*, *how telemetry flows through it*, and *how to safely modify or extend it with real SNMP/gNMI sources*.

---

## 0. Executive Summary & Architectural Purpose

The **Collection Layer** is a standalone, asynchronous Python microservice built on **FastAPI** and **HTTPX**. It acts as the decoupled ingestion buffer and normalisation gateway between raw network telemetry sources and the core NetOps backend database.

```
                    ┌────────────────────────────────────────────────────────┐
                    │                      DATA SOURCES                      │
                    │                                                        │
                    │  [Simulator Engine]   [SNMP Poller]   [gNMI Streamer]  │
                    └───────────┬───────────────────┬───────────────┬────────┘
                                │ (HTTP Push)       │ (UDP Poll)    │ (gRPC Stream)
                                ▼                   ▼               ▼
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│ collector/ (Port 8100)                                                                     │
│                                                                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ Sources Layer (app/sources/)                                                       │   │
│   │   • PushSource: exposes POST /ingest to external producers (simulator/agents)     │   │
│   │   • BaseSource: uniform lifecycle interface (start/stop) for background pollers   │   │
│   │   • SOURCE_REGISTRY: pluggable factory mapping configured names to source classes  │   │
│   └─────────────────────────────────────────┬──────────────────────────────────────────┘   │
│                                             │ IngestRequest                                │
│                                             ▼                                              │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ CollectorService (app/service.py)                                                  │   │
│   │   • Central stateful coordinator managing lifecycle of sources & forwarders        │   │
│   │   • Normalises incoming telemetry into validated SampleRecord models               │   │
│   │   • Maintains running observability counters (received, accepted, failures)        │   │
│   └─────────────────────────────────────────┬──────────────────────────────────────────┘   │
│                                             │ list[SampleRecord]                           │
│                                             ▼                                              │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐   │
│   │ Forwarders Layer (app/forwarders/)                                                 │   │
│   │   • BackendForwarder: batches & POSTs with retry/backoff to Backend API            │   │
│   │   • LogForwarder: zero-I/O dry-run sink for offline validation and testing        │   │
│   │   • FORWARDER_REGISTRY: pluggable factory for downstream destinations              │   │
│   └─────────────────────────────────────────┬──────────────────────────────────────────┘   │
└─────────────────────────────────────────────┼──────────────────────────────────────────────┘
                                              │ HTTP POST /api/v1/telemetry/ingest
                                              ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               CORE BACKEND API (Port 8000)             │
                    │        (FastAPI + SQLAlchemy Async + MySQL 8.0)        │
                    └────────────────────────────────────────────────────────┘
```

### Why does the collector exist?

1. **Decoupling Sources from Business Logic:**  
   The core backend API (`backend/`) is responsible for NOC domain entities, database persistence, REST queries, alerts, and AI Copilot reasoning. It should never know or care whether incoming interface bytes came from a Python mock simulator, an enterprise Cisco router polled via SNMPv3, or an Arista switch streaming gNMI state over gRPC.
2. **Pluggable Ingestion Pipeline:**  
   In local development, the collection layer runs with `COLLECTOR_SOURCES=push` to receive HTTP batches from `simulator/`. In production, you change the configuration to `COLLECTOR_SOURCES=snmp` or `COLLECTOR_SOURCES=gnmi` without altering a single line of backend code or database schemas.
3. **Resilience & Rate Smoothing:**  
   The collector provides batching, exponential retry backoff, and failure isolation. If the database backend experiences a transient hiccup or migration restart, the collector absorbs the ingestion requests, retries safely, and reports transparent metrics.
4. **Isolated Dry-Run Validation:**  
   Setting `COLLECTOR_FORWARDER=log` or `COLLECTOR_DRY_RUN=true` allows developers to test source ingestion end-to-end without writing a single row to MySQL.

---

## 1. Directory Tree & File Inventory

Here is the complete layout of the `collector/` directory:

```
collector/
├── app/
│   ├── __init__.py                # Package version (__version__ = "0.1.0")
│   ├── __main__.py                # Entrypoint for `python -m app` (starts Uvicorn)
│   ├── config.py                  # Pydantic BaseSettings (COLLECTOR_* environment variables)
│   ├── main.py                    # FastAPI application factory, CORS, and async lifespan
│   ├── models.py                  # Pydantic schemas (SampleRecord, IngestRequest, etc.)
│   ├── service.py                 # CollectorService orchestration and running metrics
│   ├── core/
│   │   ├── __init__.py            # Core package marker
│   │   ├── errors.py              # Typed exception hierarchy (CollectorError, ForwardError, etc.)
│   │   └── logging.py             # Structured log formatters (JSON & ANSI text)
│   ├── forwarders/
│   │   ├── __init__.py            # Re-exports BaseForwarder, build_forwarder, registries
│   │   ├── base.py                # Abstract BaseForwarder class definition
│   │   ├── backend.py             # BackendForwarder: chunked HTTP POST with retry
│   │   ├── log_forwarder.py       # LogForwarder: offline dry-run logger
│   │   └── registry.py            # Forwarder factory and registration catalog
│   ├── routes/
│   │   ├── __init__.py            # Routes package marker
│   │   ├── health.py              # GET /health and GET /metrics endpoints
│   │   └── ingest.py              # POST /ingest endpoint with optional API key security
│   └── sources/
│       ├── __init__.py            # Re-exports BaseSource, build_sources, registries
│       ├── base.py                # Abstract BaseSource class definition
│       ├── push.py                # PushSource: HTTP push adapter
│       └── registry.py            # Source factory and registration catalog
├── tests/
│   ├── __init__.py                # Tests package marker
│   ├── helpers.py                 # FakeForwarder and factory fixtures for deterministic tests
│   ├── test_api.py                # HTTP integration tests (TestClient for /health, /metrics, /ingest)
│   ├── test_models.py             # Pydantic validation and datetime parsing tests
│   └── test_service.py            # Unit tests for CollectorService state and forwarding logic
├── pytest.ini                     # Pytest configuration (asyncio_mode = auto, pythonpath = .)
├── requirements.txt               # Production runtime dependencies
└── requirements-dev.txt           # Development and test dependencies
```

---

## 2. In-Depth Walkthrough of Every Single File

### 2.1 Configuration & Dependency Files

#### `collector/requirements.txt`
Specifies the minimal production runtime dependencies needed to run the microservice:
- `fastapi >= 0.115.0`: High-performance asynchronous web framework for HTTP routes.
- `uvicorn[standard] >= 0.30.0`: Production ASGI web server with uvloop and httptools.
- `pydantic >= 2.8.0` & `pydantic-settings >= 2.4.0`: Type validation, strict coercion, and environment variable parsing.
- `httpx >= 0.27.0`: Production-grade asynchronous HTTP client used by forwarders to communicate with downstream services.
- `python-dotenv >= 1.0.0`: Loads configuration from local `.env` and root `.env` files automatically.

#### `collector/requirements-dev.txt`
Extends `requirements.txt` with developer testing utilities:
- `-r requirements.txt`: Includes all runtime packages.
- `pytest >= 8.3.0`: Unit and integration test runner.
- `pytest-asyncio >= 0.24.0`: Async fixture and coroutine test execution without manual loop management.
- `anyio >= 4.4.0`: Structured concurrency backend used by Starlette and TestClient.

#### `collector/pytest.ini`
Configures pytest execution flags:
```ini
[pytest]
asyncio_mode = auto
pythonpath = .
testpaths = tests
```
- `asyncio_mode = auto`: Allows marking tests as `async def test_*` directly without `@pytest.mark.asyncio`.
- `pythonpath = .`: Ensures `app` and `tests` packages are resolvable on `sys.path` when running from the `collector/` root.

---

### 2.2 Root Application Files (`app/`)

#### `app/__init__.py`
Defines package metadata and version string:
```python
__version__ = "0.1.0"
```

#### `app/__main__.py`
The CLI launcher for the collection service. Executed when invoking:
```bash
python -m app
```
It reads settings via `get_settings()` and starts `uvicorn.run("app.main:create_app", factory=True, host=settings.host, port=settings.port, reload=False)`. Using `factory=True` instructs Uvicorn to call `create_app()` inside worker processes.

#### `app/config.py`
Centralized settings management using Pydantic's `BaseSettings`. No hardcoded values exist anywhere else in the application.

- **Settings Class:**
  - `host: str = "0.0.0.0"`: Bind address.
  - `port: int = 8100`: Microservice listening port (distinct from backend port 8000).
  - `sources: str = "push"`: Comma-separated list of active sources (e.g. `"push"`, `"push,snmp"`).
  - `active_sources -> list[str]`: Computed property parsing the comma-separated string into a clean lowercase list.
  - `forwarder: str = "backend"`: Selected forwarder name (`"backend"` or `"log"`).
  - `forward_url: str = "http://localhost:8000/api/v1/telemetry/ingest"`: Downstream backend ingest URL.
  - `timeout_seconds: float = 10.0`: HTTP timeout for backend forwarding.
  - `max_retries: int = 3`: Maximum retry attempts on network transport failures.
  - `retry_backoff_seconds: float = 0.5`: Base delay for exponential backoff.
  - `batch_size: int = 200`: Max sample records per forward HTTP chunk.
  - `poll_interval_seconds: float = 30.0`: Polling frequency for future background sources.
  - `api_key: str = ""`: Optional shared secret header `X-Collector-Key`. When blank, authentication is bypassed (ideal for local dev).
  - `dry_run: bool = False`: Forces the forwarder to `LogForwarder` regardless of the `forwarder` setting.
  - `log_level: str = "INFO"`: Log severity threshold.
- **Factory:**
  `get_settings() -> Settings`: Instantiates fresh settings, checking `./.env` and `../.env`.

#### `app/models.py`
Data schemas representing telemetry contracts and API responses:

1. `SampleRecord(BaseModel)`:
   - `interface_id: int`: Foreign key referencing the `interfaces` table in the database.
   - `rx_bytes: int`: Received bytes delta over the sampling interval ($\ge 0$).
   - `tx_bytes: int`: Transmitted bytes delta over the sampling interval ($\ge 0$).
   - `packet_drops: int`: Number of dropped packets ($\ge 0$).
   - `errors: int`: Number of transmission or framing errors ($\ge 0$).
   - `measured_at: datetime`: Timestamp when the sample was recorded. Includes a custom `@field_validator("measured_at", mode="before")` that handles ISO 8601 strings and attaches UTC timezone if missing.
   - `as_backend_body() -> dict`: Formats the record into the wire format expected by the backend API:
     ```python
     {
         "interface_id": self.interface_id,
         "rx_bytes": self.rx_bytes,
         "tx_bytes": self.tx_bytes,
         "packet_drops": self.packet_drops,
         "errors": self.errors,
         "measured_at": self.measured_at.isoformat(),
     }
     ```
2. `IngestRequest(BaseModel)`:
   - `source: str = "unknown"`: Human-readable identifier for the origin (e.g. `"simulator"`, `"snmp-poller"`).
   - `samples: list[SampleRecord] = []`: The list of samples in this batch.
3. `IngestResponse(BaseModel)`:
   - `success: bool = True`
   - `data: dict = {}`: Contains downstream forwarder acknowledgement details, such as `{"accepted": 12, "batches": 1}`.
4. `HealthResponse(BaseModel)`:
   - `status: str = "ok"`
   - `version: str`: Current microservice version.
   - `sources: list[str]`: Currently active source names.
   - `forwarder: str`: Active forwarder destination.
   - `uptime_seconds: float`: Time elapsed since service startup.

#### `app/service.py`
`CollectorService` is the heartbeat of the microservice. It wires the source inputs to the downstream forwarder and maintains runtime metrics.

- **Initialization:**
  Takes `sources: list[BaseSource]` and `forwarder: BaseForwarder`. Initializes metrics counters:
  - `self.received = 0`: Total samples received across all calls.
  - `self.accepted = 0`: Total samples successfully confirmed by the forwarder.
  - `self.failures = 0`: Total failed batch delivery attempts.
- **`start() -> None`:**
  Records `_started_at` time via `time.monotonic()`. Loops over each registered source and calls `await source.start(self)`.
- **`stop() -> None`:**
  Gracefully halts all sources via `await source.stop()`, then releases forwarder HTTP connections via `await self._forwarder.close()`.
- **`receive(request: IngestRequest) -> dict`:**
  Called by sources whenever a telemetry batch is available.
  1. Increments `self.received += len(request.samples)`.
  2. If empty, returns immediately with `{"accepted": 0}`.
  3. Hands the sample list to the forwarder: `await self._forwarder.send(samples)`.
  4. Increments `self.accepted += result.get("accepted", 0)`.
  5. If a `ForwardError` is caught, increments `self.failures += 1` and re-raises so the API route or source can respond accordingly.

#### `app/main.py`
The FastAPI application factory:

- **`_lifespan(app: FastAPI)` Context Manager:**
  Manages startup and shutdown hooks cleanly using FastAPI's lifespan API:
  1. Configures logging with the specified log level.
  2. Instantiates active sources via `build_sources(settings.active_sources)`.
  3. Instantiates the configured forwarder via `build_forwarder(settings)`.
  4. Instantiates `CollectorService` and attaches it to `app.state.service`.
  5. Calls `await service.start()`.
  6. Yields execution to serve HTTP traffic.
  7. On application shutdown, calls `await service.stop()`.
- **`create_app(settings: Settings | None = None) -> FastAPI`:**
  - Instantiates `FastAPI(title="NetOps Collection Layer", version=__version__, lifespan=_lifespan)`.
  - Attaches `settings` to `app.state.settings`.
  - Configures CORS middleware.
  - Registers exception handlers: translates `CollectorError` into structured JSON responses with HTTP 502/500 status codes.
  - Includes routers: `health_router` and `ingest_router`.

---

### 2.3 Cross-Cutting Utilities (`app/core/`)

#### `app/core/logging.py`
Provides consistent structured logging across the collector:
- `JsonFormatter`: Emits machine-readable single-line JSON logs containing timestamp, level, message, logger name, and extra context fields (`stage`, `source`, `batch_size`, `accepted`).
- `TextFormatter`: Emits clean, readable terminal logs with timestamps and contextual tags.
- `configure_logging(level, json_logs=False)`: Configures the root logger and dampens noisy third-party loggers (`httpx`, `httpcore`, `uvicorn.access`).
- `get_logger(name)`: Convenience wrapper returning a standard Python `logging.Logger`.

#### `app/core/errors.py`
Typed exception hierarchy:
- `CollectorError(Exception)`: Base exception for all collection layer errors. Accepts an optional `stage` attribute (e.g. `"source"`, `"service"`, `"forwarder"`).
- `ConfigurationError(CollectorError)`: Raised on invalid configuration, such as an unknown source name or unknown forwarder name.
- `SourceError(CollectorError)`: Raised when a telemetry source encounters an unrecoverable failure.
- `ForwardError(CollectorError)`: Raised when forwarding telemetry to the backend fails. Includes `status_code` and response snippet if available.

---

### 2.4 Ingestion Sources (`app/sources/`)

#### `app/sources/base.py`
The abstract contract for telemetry sources:
```python
class BaseSource(ABC):
    name: str = "base"

    @abstractmethod
    async def start(self, service: CollectorService) -> None:
        """Initialize the source (e.g., launch background polling tasks)."""

    @abstractmethod
    async def stop(self) -> None:
        """Tear down the source (cancel background tasks, close sockets)."""
```

#### `app/sources/push.py`
`PushSource(BaseSource)`:
- `name = "push"`
- Used when external processes (such as the simulator or network sidecars) push metrics over HTTP POST.
- Because HTTP routing is handled by FastAPI routers (`app/routes/ingest.py`), `start()` and `stop()` simply log lifecycle transitions.

#### `app/sources/registry.py`
Registry mapping source identifiers to implementation classes:
- `SOURCE_REGISTRY: dict[str, type[BaseSource]]`:
  Currently registers `"push": PushSource`. Provides designated extension hooks for `"snmp"`, `"gnmi"`, and `"sflow"`.
- `build_sources(active: list[str]) -> list[BaseSource]`:
  Takes a list of string identifiers (from `Settings.active_sources`), instantiates each class from the registry, and raises a clear `ConfigurationError` if any name is unknown.

---

### 2.5 Downstream Forwarders (`app/forwarders/`)

#### `app/forwarders/base.py`
The abstract contract for forwarders:
```python
class BaseForwarder(ABC):
    name: str = "base"

    @abstractmethod
    async def send(self, samples: list[SampleRecord]) -> dict:
        """Deliver samples to destination. Returns dict like {'accepted': N}."""

    async def close(self) -> None:
        """Release underlying connections or client sessions."""
```

#### `app/forwarders/backend.py`
`BackendForwarder(BaseForwarder)`:
- `name = "backend"`
- Handles delivering validated telemetry to the core backend API at `POST /api/v1/telemetry/ingest`.
- **Chunking:** Uses `_chunked(samples, self._batch_size)` (default 200) to avoid overloading the backend with massive single payloads.
- **Exponential Retry Logic (`_post_with_retry`):**
  - Retries on network-level transport exceptions (`httpx.TransportError`, `httpx.TimeoutException`).
  - Does **not** retry HTTP 4xx client errors (which signify validation issues or invalid IDs).
  - Backoff formula: $\text{delay} = \text{backoff\_seconds} \times 2^{\text{attempt} - 1}$.
  - Raises a typed `ForwardError` if all retry attempts fail.
- **Resource Management:** Owns an internal `httpx.AsyncClient` that is closed cleanly during service shutdown.

#### `app/forwarders/log_forwarder.py`
`LogForwarder(BaseForwarder)`:
- `name = "log"`
- Zero-network dry-run sink. Logs each received batch at `INFO` level (and individual sample interface IDs at `DEBUG` level).
- Returns `{"accepted": len(samples), "dry_run": True}` immediately.
- Used when running tests or debugging the pipeline offline without a running backend.

#### `app/forwarders/registry.py`
Registry and factory for forwarders:
- `FORWARDER_REGISTRY: dict[str, type[BaseForwarder]]`:
  Registers `"backend": BackendForwarder` and `"log": LogForwarder`.
- `build_forwarder(settings: Settings) -> BaseForwarder`:
  - If `settings.dry_run` is True, always returns `LogForwarder()` regardless of configured name.
  - If `settings.forwarder == "backend"`, constructs `BackendForwarder` with the configured URL, timeouts, retry parameters, and batch size.
  - Raises `ConfigurationError` for unknown forwarder names.

---

### 2.6 HTTP Routes (`app/routes/`)

#### `app/routes/health.py`
Exposes observability endpoints:
- `GET /health`:
  Returns `HealthResponse` with `status: "ok"`, `version`, list of active source names, active forwarder name, and uptime in seconds.
- `GET /metrics`:
  Returns operational counters in standard envelope format:
  ```json
  {
    "success": true,
    "data": {
      "received": 1540,
      "accepted": 1540,
      "failures": 0,
      "uptime_seconds": 128.4
    }
  }
  ```

#### `app/routes/ingest.py`
Exposes the main push ingestion endpoint:
- `POST /ingest`:
  - Accepts `IngestRequest` JSON body.
  - Includes dependency `_check_api_key`: validates `X-Collector-Key` header against `settings.api_key` if configured.
  - Obtains `CollectorService` from `request.app.state.service`.
  - Invokes `await service.receive(payload)`.
  - Returns `IngestResponse(success=True, data=result)`.

---

### 2.7 Test Suite (`tests/`)

The collector includes a comprehensive, isolated test suite that runs without external services or network calls:

1. `tests/helpers.py`:
   - `FakeForwarder(BaseForwarder)`: In-memory mock forwarder capturing sent batches in `self.sent_batches`.
   - `make_sample(interface_id=1, ...)`: Helper factory generating valid `SampleRecord` instances.
2. `tests/test_models.py`:
   - Validates `SampleRecord` instantiation, constraints ($\ge 0$ bytes/drops/errors), and automatic ISO string datetime parsing to UTC.
   - Validates `IngestRequest` defaults and sample list parsing.
3. `tests/test_service.py`:
   - Tests `CollectorService.receive()` sample delegation to forwarders.
   - Tests that empty batches are safe no-ops.
   - Verifies uptime counter increases monotonically.
4. `tests/test_api.py`:
   - Uses Starlette's `TestClient` to test `GET /health`, `GET /metrics`, and `POST /ingest` through full HTTP cycles.

To run the suite:
```bash
cd collector
.\.venv\Scripts\python.exe -m pytest tests -v
```

---

## 3. End-to-End Execution Trace: Ingesting a Telemetry Batch

Here is the exact code execution sequence when a telemetry batch arrives:

```
1. Simulator POSTs to http://localhost:8100/ingest with JSON payload:
   { "source": "simulator", "samples": [{ "interface_id": 10, "rx_bytes": 450000, ... }] }
   │
2. Uvicorn receives request and dispatches to FastAPI app (app/main.py)
   │
3. Route handler ingest() in app/routes/ingest.py is invoked:
   a. _check_api_key validates the X-Collector-Key header (if configured)
   b. Pydantic parses and validates the request body into IngestRequest
   c. Pydantic parses each item in samples into a SampleRecord, validating constraints
   │
4. Route retrieves request.app.state.service (the singleton CollectorService)
   │
5. CollectorService.receive(request) executes:
   a. Increments self.received += len(samples)
   b. Calls await self._forwarder.send(samples)
   │
6. BackendForwarder.send(samples) executes:
   a. Splits samples into chunks of size batch_size (default 200)
   b. Serializes each sample via sample.as_backend_body()
   c. Executes _post_with_retry() using internal httpx.AsyncClient:
      - POST http://localhost:8000/api/v1/telemetry/ingest
      - Body: { "samples": [ ... ] }
      - On connection timeout or transport error: sleeps with exponential backoff and retries
   d. Sums accepted sample counts from backend response
   │
7. CollectorService receives forwarder result:
   a. Increments self.accepted += result["accepted"]
   b. Returns result dictionary to route
   │
8. Route wraps result in IngestResponse and returns HTTP 200:
   { "success": true, "data": { "accepted": 1, "batches": 1 } }
```

---

## 4. How to Extend the Collection Layer

### 4.1 Adding a Real Telemetry Source (e.g. SNMP Poller)

To add periodic SNMP polling for physical routers:

1. **Create the Source File:**  
   Create `collector/app/sources/snmp.py`:
   ```python
   import asyncio
   from app.sources.base import BaseSource
   from app.models import IngestRequest, SampleRecord

   class SnmpSource(BaseSource):
       name = "snmp"

       async def start(self, service) -> None:
           self._service = service
           self._running = True
           self._task = asyncio.create_task(self._poll_loop())

       async def stop(self) -> None:
           self._running = False
           if hasattr(self, "_task"):
               self._task.cancel()

       async def _poll_loop(self) -> None:
           while self._running:
               # 1. Query device OIDs (ifInOctets, ifOutOctets, etc.)
               # 2. Build SampleRecord instances
               # 3. await self._service.receive(IngestRequest(source="snmp", samples=samples))
               await asyncio.sleep(30.0)
   ```

2. **Register in `app/sources/registry.py`:**
   ```python
   from app.sources.snmp import SnmpSource

   SOURCE_REGISTRY: dict[str, type[BaseSource]] = {
       "push": PushSource,
       "snmp": SnmpSource,
   }
   ```

3. **Activate via Environment:**  
   In `.env`:
   ```env
   COLLECTOR_SOURCES=push,snmp
   ```
   Now the collector accepts simulator pushes *and* polls SNMP devices simultaneously!

### 4.2 Adding a Message Broker Forwarder (e.g. Kafka)

To stream incoming metrics to an Apache Kafka topic instead of directly calling the backend HTTP API:

1. **Create the Forwarder File:**  
   Create `collector/app/forwarders/kafka.py`:
   ```python
   from app.forwarders.base import BaseForwarder
   from app.models import SampleRecord

   class KafkaForwarder(BaseForwarder):
       name = "kafka"

       def __init__(self, bootstrap_servers: str = "localhost:9092") -> None:
           # initialize Kafka producer client
           pass

       async def send(self, samples: list[SampleRecord]) -> dict:
           # publish samples to Kafka topic
           return {"accepted": len(samples), "destination": "kafka"}

       async def close(self) -> None:
           # flush and close producer
           pass
   ```

2. **Register in `app/forwarders/registry.py`:**
   ```python
   from app.forwarders.kafka import KafkaForwarder

   FORWARDER_REGISTRY: dict[str, type[BaseForwarder]] = {
       "backend": BackendForwarder,
       "log": LogForwarder,
       "kafka": KafkaForwarder,
   }
   ```

3. **Activate via Environment:**  
   In `.env`:
   ```env
   COLLECTOR_FORWARDER=kafka
   ```

---

## 5. Operations & Troubleshooting

### Running Locally
```powershell
# From the repository root
cd collector
.\.venv\Scripts\Activate.ps1
python -m app
```
The server will start listening on `http://0.0.0.0:8100`. Interactive OpenAPI documentation is accessible at `http://localhost:8100/docs`.

### Verifying Service Health
```powershell
curl http://localhost:8100/health
```
Expected output:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "sources": ["push"],
  "forwarder": "backend",
  "uptime_seconds": 45.2
}
```

### Inspecting Real-Time Counters
```powershell
curl http://localhost:8100/metrics
```
Expected output:
```json
{
  "success": true,
  "data": {
    "received": 240,
    "accepted": 240,
    "failures": 0,
    "uptime_seconds": 45.2
  }
}
```
If `failures > 0`, check backend logs or verify that `COLLECTOR_FORWARD_URL` points to an active backend service.

# `backend/` — Complete Code & Architecture Explanation

> **Audience:** Any developer working on NetOps backend or frontend integration.
> **Goal:** Understand every file in `backend/`, why it exists, how data flows through it, and how to safely extend it.

---

## 0. Executive Summary

The **NetOps Backend** is a high-performance asynchronous web service built with **FastAPI**. It has four primary responsibilities:
1. **RDBMS Telemetry Storage (No ORM):** Connects to MySQL 8.0 using raw `aiomysql` connection pooling. All queries are parameterised SQL constants located in [app/db/queries.py](file:///d:/Projects/netops/backend/app/db/queries.py).
2. **Collection Layer Ingestion:** Accepts metric batches via `POST /api/v1/telemetry/ingest` from the collector microservice.
3. **Dynamic ML Risk Scoring Engine:** Evaluates network health on every ingest using a two-phase formula (normalised multi-factor impact score + rolling-window Z-score statistical baseline amplifier). It automatically detects anomalies and fires alerts into the `alerts` table.
4. **RAG AI Copilot:** Retrieves real-time topology, metrics, and alerts from MySQL, builds grounded prompt templates, and queries an LLM (Mock by default, OpenAI/Ollama-ready).

---

## 1. Directory & File Blueprint

```
backend/
├── app/
│   ├── config.py              # Central Pydantic BaseSettings
│   ├── main.py                # App factory, lifespan, CORS, error handlers
│   ├── __main__.py            # CLI entrypoint for uvicorn
│   │
│   ├── core/
│   │   ├── logging.py         # Structured logging (JSON for prod, text for dev)
│   │   └── errors.py          # Typed AppError hierarchy
│   │
│   ├── db/
│   │   ├── pool.py            # aiomysql.create_pool management
│   │   ├── helpers.py         # fetch_one, fetch_many, execute, executemany
│   │   └── queries.py         # Source-of-truth SQL statements
│   │
│   ├── models/                # Pydantic v2 I/O Schemas
│   │   ├── device.py          # Device schemas
│   │   ├── interface.py       # Interface schemas
│   │   ├── metric.py          # Ingest & metric schemas
│   │   ├── alert.py           # Alert schemas
│   │   ├── score.py           # Risk score breakdown schemas
│   │   └── copilot.py         # Copilot chat schemas
│   │
│   ├── scoring/               # Dynamic ML Scoring Engine
│   │   ├── formula.py         # score_interface() math and Z-scores
│   │   └── detector.py        # Post-ingest anomaly detector & alert trigger
│   │
│   ├── rag/                   # Grounded Copilot Pipeline
│   │   ├── context.py         # Database context retriever
│   │   ├── prompt.py          # Versioned prompt templates
│   │   └── llm.py             # LLM provider abstraction (Mock / OpenAI / Ollama)
│   │
│   └── routers/               # REST API Handlers
│       ├── deps.py            # FastAPI dependency injection
│       ├── devices.py         # /devices endpoints
│       ├── interfaces.py      # /interfaces endpoints (including /score)
│       ├── telemetry.py       # /telemetry/ingest endpoint
│       ├── alerts.py          # /alerts endpoints
│       ├── copilot.py         # /copilot/chat & history endpoints
│       └── health.py          # /health probe endpoint
```

---

## 2. In-Depth Component Walkthrough

### 2.1 Database Layer (Raw SQL, No ORM)

- **Why no ORM?** ORMs introduce abstraction overhead, N+1 query traps, and obscure connection handling. For high-frequency network telemetry time-series workloads, raw parameterised SQL guarantees deterministic performance, predictable memory usage, and direct alignment with MySQL 8.0 indexing.
- **[app/db/pool.py](file:///d:/Projects/netops/backend/app/db/pool.py):** Initializes an `aiomysql.Pool` once during FastAPI lifespan startup, bound to `app.state.pool`. Shuts it down cleanly on SIGTERM/SIGINT.
- **[app/db/helpers.py](file:///d:/Projects/netops/backend/app/db/helpers.py):** Provides `acquire()`, `fetch_one()`, `fetch_many()`, `execute()`, and `executemany()`. Cursor management and exception wrapping (`DatabaseError`) are centralized here.
- **[app/db/queries.py](file:///d:/Projects/netops/backend/app/db/queries.py):** Every query is an uppercase constant. No SQL string literals exist anywhere else in the backend.

### 2.2 Dynamic Risk Scoring Formula

Instead of rigid static thresholds (e.g. `if drops > 10`), the scoring engine in [app/scoring/formula.py](file:///d:/Projects/netops/backend/app/scoring/formula.py) evaluates metrics dynamically:

1. **Phase 1 — Normalised Impact Score ($I \in [0, 1]$):**
   $$I = \text{clamp}(W_{\text{util}} \cdot U + W_{\text{drop}} \cdot D + W_{\text{error}} \cdot E + W_{\text{trend}} \cdot T)$$
   - $U$: Interface utilisation relative to capacity (`speed_bps`).
   - $D$: Packet drop rate normalised against estimated packet volume (`rx_bytes / 1400`).
   - $E$: Error rate per byte (normalised to $10^{-4}$ saturation limit).
   - $T$: Directional traffic trend slope over the window.

2. **Phase 2 — Statistical Baseline Z-score Amplifier:**
   - Computes rolling mean $\mu$ and standard deviation $\sigma$ across the historical window for each interface.
   - Computes $Z = \frac{|x_{\text{latest}} - \mu|}{\sigma}$.
   - If historical baseline has zero variance ($\sigma \approx 0$) and a spike occurs, $Z$ is amplified ($Z \ge 10.0$).
   - If $\max(Z) > \text{threshold}$, the anomaly flag is set, and severity is amplified:
     $$\text{Severity} = \text{clamp}\left(I \cdot \left(1 + 0.5 \cdot \text{clamp}\left(\frac{\max(Z)}{\sigma_{\text{threshold}}} - 1\right)\right)\right)$$

3. **Classification:**
   - $\ge 0.80$: `CRITICAL`
   - $\ge 0.60$: `HIGH`
   - $\ge 0.30$: `MEDIUM`
   - $< 0.30$: `LOW`

### 2.3 Post-Ingest Anomaly Detector & Alerting

- **[app/scoring/detector.py](file:///d:/Projects/netops/backend/app/scoring/detector.py):**
  - Triggered after every batch write in `POST /telemetry/ingest`.
  - For each affected interface, pulls its recent scoring window.
  - If anomalous, checks `ALERT_RECENT_UNRESOLVED` to prevent duplicate alert storms within 5 minutes.
  - Inserts new alerts into the `alerts` table.

### 2.4 Grounded RAG Copilot Pipeline

- **[app/rag/context.py](file:///d:/Projects/netops/backend/app/rag/context.py):** Queries MySQL for the device/interface metadata, the latest telemetry samples, and recent unresolved alerts.
- **[app/rag/prompt.py](file:///d:/Projects/netops/backend/app/rag/prompt.py):** Formats the retrieved context into a structured Markdown system prompt, instructing the model to ground all assertions strictly in the supplied data.
- **[app/rag/llm.py](file:///d:/Projects/netops/backend/app/rag/llm.py):** Pluggable client:
  - `mock`: Returns simulated responses instantly without external network calls or API keys.
  - `openai`: Connects to any OpenAI-compatible API endpoint with bearer auth.
  - `ollama`: Connects to local Ollama daemon for offline self-hosted inference.

---

## 3. End-to-End Pipeline Execution

The pipeline was validated live against MySQL 8.0:
1. **Simulator:** Emits multi-scenario telemetry for 19 interfaces.
2. **Collector (Port 8100):** Receives samples on `POST /ingest` and forwards to backend.
3. **Backend (Port 8000):** Receives samples on `POST /api/v1/telemetry/ingest`, inserts them into `interface_metrics`, runs `run_detection()`, and persists triggered alerts.
4. **Result:** 95 time-series metrics written and 23 dynamic alerts generated with zero dropped packets.

# NetOps Backend Service

The NetOps backend is a **FastAPI** service with a **pure RDBMS focus** (no ORM, raw `aiomysql` queries), dynamic multi-factor ML risk scoring, and a grounded RAG Copilot pipeline.

---

## Key Features

1. **Pure RDBMS (No ORM)**
   - Utilizes `aiomysql` connection pooling.
   - All SQL queries are parameterised and isolated in [app/db/queries.py](file:///d:/Projects/netops/backend/app/db/queries.py).
   - Zero SQL injection vulnerability and maximum query execution performance.

2. **Telemetry Ingest & Collection Layer Connection**
   - Ingests batch telemetry from either the `simulator` or real collectors (SNMP/gNMI) via the `collector` service.
   - Bulk-inserts time-series records into `interface_metrics`.
   - Triggers the dynamic anomaly detector on every ingested interface.

3. **Dynamic ML Risk Scoring Engine**
   - **Phase 1: Impact Scoring (0..1)**
     - Link Utilisation (weight = 0.30)
     - Packet Drop Rate (weight = 0.40)
     - Error Rate (weight = 0.20)
     - Traffic Trend Slope (weight = 0.10)
   - **Phase 2: Baseline Z-Score Statistical Amplifier**
     - Calculates rolling mean and standard deviation over historical window.
     - Detects deviations ($\sigma > 3.0$) and scales severity score.
     - Flags anomalies and creates de-duplicated alerts automatically.

4. **RAG AI Copilot Pipeline**
   - Dynamic context retriever queries recent telemetry, active alerts, and device topology from MySQL.
   - Versioned prompt templates inject grounded context into LLM system prompts.
   - Pluggable provider architecture: `mock` (default for dev), `openai`, `ollama`, or `local`.

5. **Frontend-Ready REST API & CORS**
   - Configured CORS for Vite/React dev ports (`http://localhost:5173`, `http://localhost:3000`).
   - Clean Pydantic request/response schemas for easy frontend TypeScript type generation.
   - Interactive OpenAPI documentation at `http://localhost:8000/docs`.

---

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── __main__.py              # Entrypoint: python -m app
│   ├── config.py                # Pydantic Settings (env vars)
│   ├── main.py                  # FastAPI factory, lifespan, CORS & router registration
│   ├── core/
│   │   ├── errors.py            # Typed exceptions -> HTTP status codes
│   │   └── logging.py           # Structured JSON / coloured text logging
│   ├── db/
│   │   ├── pool.py              # aiomysql connection pool creation
│   │   ├── helpers.py           # acquire, fetch_one, fetch_many, execute, executemany
│   │   └── queries.py           # Parameterised SQL statements
│   ├── models/
│   │   ├── device.py            # Device Pydantic schemas
│   │   ├── interface.py         # Interface Pydantic schemas
│   │   ├── metric.py            # Telemetry ingest & metric schemas
│   │   ├── alert.py             # Alert list and resolve schemas
│   │   ├── copilot.py           # Chat message & response schemas
│   │   └── score.py             # Live risk score breakdown schemas
│   ├── routers/
│   │   ├── deps.py              # FastAPI dependencies (pool, settings, llm)
│   │   ├── devices.py           # GET /devices, GET /devices/{id}, /devices/{id}/interfaces
│   │   ├── interfaces.py        # GET /interfaces/{id}, /metrics, /score
│   │   ├── telemetry.py         # POST /telemetry/ingest
│   │   ├── alerts.py            # GET /alerts, PATCH /alerts/{id}/resolve
│   │   ├── copilot.py           # POST /copilot/chat, GET /copilot/history/{id}
│   │   └── health.py            # GET /health
│   ├── scoring/
│   │   ├── formula.py           # Multi-factor impact + Z-score baseline math
│   │   └── detector.py          # Post-ingest anomaly detector & alert trigger
│   └── rag/
│       ├── context.py           # MySQL context retriever
│       ├── prompt.py            # Versioned prompt builders
│       └── llm.py               # LLM clients (Mock, OpenAI, Ollama)
├── tests/                       # Pytest test suite (scoring, models, rag)
├── requirements.txt
└── explanation.md
```

---

## Running the Service

### 1. Start MySQL
```bash
docker compose up -d
```

### 2. Start the Backend
```bash
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```

### 3. Run Tests
```bash
.venv\Scripts\python.exe -m pytest tests/ -v
```

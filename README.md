# NetOps — Network Operations Center & AI Copilot Platform

[![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6.svg)](https://www.typescriptlang.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1.svg)](https://www.mysql.com/)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF.svg)](https://vitejs.dev/)

A modern, production-structured Network Operations Center (NOC) platform. NetOps provides real-time network device inventory management, high-throughput time-series telemetry ingestion, automated anomaly detection, interactive topology visualization, and an AI Copilot grounded in live network telemetry.

---

## 1. System Architecture

NetOps is designed as a decoupled, multi-tier microservice architecture where telemetry collection, domain management, persistence, simulation, and presentation are strictly segregated.

```
                                  DATA PRODUCERS
                                  ==============
           ┌────────────────────────────┐      ┌────────────────────────────┐
           │     simulator/ (Engine)    │      │    Physical Infrastructure │
           │ (Scenarios & Generators)   │      │   (Cisco / Arista / Juniper│
           └─────────────┬──────────────┘      └─────────────┬──────────────┘
                         │ (HTTP Push)                       │ (SNMP / gNMI)
                         ▼                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ collector/ — Telemetry Collection Layer (Port 8100)                                     │
│   • FastAPI microservice buffering and normalizing all incoming telemetry              │
│   • Pluggable Sources: PushSource (HTTP), with extension points for SNMP & gNMI        │
│   • Pluggable Forwarders: BackendForwarder (HTTP retry/backoff), LogForwarder (dry-run)│
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │ POST /api/v1/telemetry/ingest
                                         ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ backend/ — Core Application & Domain API (Port 8000)                                   │
│   • FastAPI + Pure RDBMS (raw aiomysql connection pool — no ORM overhead)              │
│   • Dynamic multi-factor ML risk scoring formula + statistical Z-score amplifier       │
│   • Automated anomaly detection & alert lifecycle management                           │
│   • Grounded RAG Copilot service: live telemetry context retrieval & LLM abstraction   │
└───────────────────┬────────────────────────────────────────────────┬───────────────────┘
                    │                                                ▲
           aiomysql │ (Async Parameterised SQL Reads & Writes)       │ REST / SSE
                    ▼                                                │
┌──────────────────────────────────────┐        ┌────────────────────┴───────────────────┐
│ database/ — Persistence (Port 3306)  │        │ frontend/ — NOC Dashboard (Port 5173)  │
│   • MySQL 8.0 InnoDB                 │        │   • React 18 + TypeScript + Vite       │
│   • Normalized 3NF Schema            │        │   • Tailwind CSS + Recharts + Lucide   │
│   • Time-series composite indexes    │        │   • Live topology graphs & metrics     │
│   • Alembic migration tracking       │        │   • Real-time AI Copilot chat drawer   │
└──────────────────────────────────────┘        └────────────────────────────────────────┘
```

### Decoupled Data Flow
1. **Telemetry Ingestion:**  
   The `simulator/` produces simulated link utilization, packet drops, and CRC errors. It pushes these to the collection layer at `http://localhost:8100/ingest`. (In production, physical network collectors replace the simulator without altering the collection layer).
2. **Buffering & Forwarding:**  
   The `collector/` validates payloads into `SampleRecord` schemas, updates local telemetry counters, and forwards chunks to `backend/` at `POST http://localhost:8000/api/v1/telemetry/ingest` with exponential retry backoff.
3. **Storage & Alerts:**  
   The `backend/` writes samples into the `interface_metrics` table in MySQL and triggers anomaly detection algorithms to register alerts if packet drops or errors breach thresholds.
4. **Monitoring & AI Copilot:**  
   Network engineers monitor live interfaces on the `frontend/` dashboard and query the AI Copilot for root-cause analysis (e.g., *"Why is R1 Gi0/1 dropping packets?"*).

---

## 2. Repository Layout

```
netops/
├── backend/                  # Core FastAPI API, SQLAlchemy Async models, Alembic migrations
│   ├── alembic/              # Database migration scripts
│   ├── app/                  # Application core, routers, models, services, AI Copilot
│   ├── tests/                # Backend unit and integration test suite
│   ├── requirements.txt      # Production runtime dependencies
│   └── requirements-dev.txt  # Dev dependencies (pytest, pytest-asyncio, etc.)
│
├── collector/                # Standalone Telemetry Collection Layer (Port 8100)
│   ├── app/                  # FastAPI app, sources (push), forwarders (backend, log), service
│   ├── tests/                # Isolated collector unit and API tests
│   ├── explanation.md        # Comprehensive collector architecture & code explanation
│   ├── requirements.txt      # Collector runtime dependencies
│   └── requirements-dev.txt  # Collector test dependencies
│
├── database/                 # Canonical MySQL 8.0 schema and seed definitions
│   ├── schema/               # Canonical DDL (schema.sql)
│   ├── migrations/           # Versioned SQL migrations (0001_initial_schema.sql, alembic_init.sql)
│   ├── seeds/                # Demo network topology matching simulator blueprint (seed_topology.sql)
│   ├── explanation.md        # Comprehensive schema, table, index, and ERD documentation
│   └── README.md             # Database reset and quick-start instructions
│
├── frontend/                 # React 18 + TypeScript + Vite + Tailwind CSS Single-Page Application
│   ├── src/                  # React components, pages, hooks, API client, charts
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies and scripts
│   └── vite.config.ts        # Vite build and proxy configuration
│
├── simulator/                # Standalone Telemetry Simulation Microservice
│   ├── app/                  # CLI, runner, engine, scenarios, generators, sinks, HTTP clients
│   ├── tests/                # 52 unit tests covering all generators, scenarios, and sinks
│   ├── explanation_simulator.md # Comprehensive simulator architecture & code explanation
│   ├── requirements.txt      # Simulator runtime dependencies
│   └── requirements-dev.txt  # Simulator test dependencies
│
├── docker-compose.yml        # Multi-container orchestration (MySQL, Backend, Collector, Frontend, Simulator)
├── .env.example              # Central configuration template
├── .gitignore                # Git ignore patterns
└── README.md                 # ← This document
```

---

## 3. Services, Ports & Endpoints

| Service | Technology | Port | Primary Endpoints |
|---|---|---|---|
| **Frontend** | React 18 + Vite | `5173` | `http://localhost:5173` |
| **Backend API** | FastAPI + SQLAlchemy | `8000` | OpenAPI docs: `http://localhost:8000/docs`<br>Devices: `/api/v1/devices`<br>Metrics Ingest: `/api/v1/telemetry/ingest`<br>Alerts: `/api/v1/alerts`<br>Copilot Chat: `/api/v1/copilot/chat` |
| **Collector Layer** | FastAPI + HTTPX | `8100` | OpenAPI docs: `http://localhost:8100/docs`<br>Push Ingest: `POST /ingest`<br>Health Check: `GET /health`<br>Live Counters: `GET /metrics` |
| **Simulator** | Python Async Engine | *N/A* | CLI Client generating background network traffic |
| **Database** | MySQL 8.0 | `3306` | Native MySQL connection (`netops` database) |

---

## 4. Prerequisites & Environment Setup

### Prerequisites
- **Python:** 3.12+ (tested up to 3.14)
- **Node.js:** 18+ (tested with Node 24.x and npm 11.x)
- **Docker & Docker Compose:** For running MySQL and containerized services
- **MySQL Client:** (Optional, for direct CLI queries)

### 4.1 Clone Repository and Configure Environment
```bash
# Clone the repository
git clone https://github.com/your-org/netops.git
cd netops

# Create root .env file from template
cp .env.example .env
```

---

## 5. Quick Start (Step-by-Step)

### Step 1: Start MySQL Database
Using Docker Compose:
```powershell
docker compose up -d mysql
```

Initialize the schema and seed topology:
```powershell
# Windows PowerShell
Get-Content database/schema/schema.sql | docker exec -i netops-mysql mysql -u netops -pnetops netops
Get-Content database/seeds/seed_topology.sql | docker exec -i netops-mysql mysql -u netops -pnetops netops
```
*(On Linux/macOS, use `cat database/schema/schema.sql | docker exec -i netops-mysql mysql -u netops -pnetops netops`)*

---

### Step 2: Start the Core Backend API (Port 8000)
Open a new terminal:
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Start API server
python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
```
*Backend is now live at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.*

---

### Step 3: Start the Collection Layer (Port 8100)
Open a new terminal:
```powershell
cd collector
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt

# Start collection server
python -m app
```
*Collector is now listening on `http://localhost:8100`. Verify health at `http://localhost:8100/health`.*

---

### Step 4: Start the Telemetry Simulator
Open a new terminal:
```powershell
cd simulator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt

# Start simulation with the default realistic mixed scenario (5s tick interval)
python -m app --scenario mixed --interval 5
```
*The simulator will discover devices via the backend, and begin pushing live telemetry batches through the collection layer.*

---

### Step 5: Start the Frontend UI (Port 5173)
Open a new terminal:
```powershell
cd frontend
npm install
npm run dev
```
*Open your browser and navigate to `http://localhost:5173`.*

---

## 6. Running with Docker Compose (Full Stack)

To run the entire platform in Docker containers:
```bash
docker compose up --build
```
This starts:
- `mysql`: Database initialized with schema and seed data
- `backend`: Core API on port 8000 (healthcheck-gated on MySQL)
- `collector`: Collection layer on port 8100 (starts after backend is healthy)
- `simulator`: Generating live telemetry in the background (starts after collector is healthy); live status dashboard on **http://localhost:8200**
- `frontend`: Dashboard served by nginx on **http://localhost:3000** (proxies `/api/` to the backend)

Every HTTP service exposes a browsable root, so you can see what is going on
just by opening its port in a browser:

| Port | URL | What you see |
|---|---|---|
| 3000 | http://localhost:3000 | NOC dashboard (React) |
| 8000 | http://localhost:8000 | Backend service index → links to `/docs`, `/health`, API routes |
| 8100 | http://localhost:8100 | Collector service index → links to `/docs`, `/health`, `/metrics` |
| 8200 | http://localhost:8200 | Simulator live status dashboard (ticks / samples / accepted, auto-refresh) |

> **Note:** a root `.env` is optional for Docker — `docker compose up` works without it
> (copy `.env.example` to `.env` only if you want to override defaults or add LLM API keys).

---

## 7. Verification & Automated Test Suites

NetOps includes isolated test suites for each Python microservice and typechecking for the frontend.

### 7.1 Backend Tests
```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -v
```

### 7.2 Collector Tests
Tests the collector service, Pydantic data schemas, retry mechanisms, and API endpoints:
```powershell
cd collector
.\.venv\Scripts\python.exe -m pytest tests -v
```
*(All 10 tests run in-memory without external dependencies).*

### 7.3 Simulator Tests
Tests all 8 traffic generators, scenarios, chunking, retry envelopes, and clock abstractions:
```powershell
cd simulator
.\.venv\Scripts\python.exe -m pytest tests -v
```
*(All 52 tests run deterministically with zero network I/O).*

### 7.4 Frontend Typechecking & Build
```powershell
cd frontend
npm run typecheck
npm run build
```

---

## 8. Deep-Dive Documentation Index

For comprehensive, file-by-file explanations of each subsystem, consult their dedicated documentation guides:

- [**`collector/explanation.md`**](file:///d:/Projects/netops/collector/explanation.md): Deep architectural dive into the Collection Layer, `CollectorService`, sources, forwarders, retry logic, and instructions on implementing SNMP/gNMI pollers.
- [**`database/explanation.md`**](file:///d:/Projects/netops/database/explanation.md): Exhaustive breakdown of the 5 MySQL tables (`devices`, `interfaces`, `interface_metrics`, `alerts`, `chat_messages`), 3NF design, composite indexing strategy, foreign key cascades, ERD diagram, and Alembic workflow.
- [**`simulator/explanation_simulator.md`**](file:///d:/Projects/netops/simulator/explanation_simulator.md): Complete guide to the Telemetry Simulator, covering all generators (`normal`, `high_traffic`, `packet_drops`, `errors`, `spikes`, `failures`), scenario routing, topology resolution, dual HTTP clients, and dry-run debugging.

---

## 9. Key Environment Variables Reference

| Variable | Service | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Backend | `mysql+aiomysql://netops:netops@localhost:3306/netops` | MySQL async connection string |
| `COLLECTOR_PORT` | Collector | `8100` | Port for the collection microservice |
| `COLLECTOR_SOURCES` | Collector | `push` | Active telemetry sources (`push`, `snmp`, `gnmi`) |
| `COLLECTOR_FORWARDER` | Collector | `backend` | Destination forwarder (`backend`, `log`) |
| `COLLECTOR_FORWARD_URL` | Collector | `http://localhost:8000/api/v1/telemetry/ingest` | Backend endpoint for validated telemetry |
| `COLLECTOR_DRY_RUN` | Collector | `false` | When true, logs telemetry without posting |
| `SIMULATOR_API_BASE_URL` | Simulator | `http://localhost:8000/api/v1` | Backend API for device & interface discovery |
| `SIMULATOR_COLLECTOR_URL` | Simulator | `http://localhost:8100/ingest` | Collection layer endpoint for telemetry injection |
| `SIMULATOR_INTERVAL_SECONDS` | Simulator | `5.0` | Simulated time duration per tick |
| `SIMULATOR_DEFAULT_SCENARIO`| Simulator | `mixed` | Active simulation scenario |
| `SIMULATOR_PORT` | Simulator | `8200` | Browsable status endpoint (`/`, `/status`, `/health`) |

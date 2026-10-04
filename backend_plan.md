# Backend Architecture Plan

## File tree (no ORM — raw SQL with aiomysql)

```
backend/
├── app/
│   ├── __init__.py
│   ├── __main__.py              # python -m app → uvicorn
│   ├── config.py                # Settings (pydantic-settings, all env vars)
│   ├── main.py                  # FastAPI factory + lifespan
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── pool.py              # aiomysql connection pool (raw SQL only)
│   │   ├── queries.py           # Named parameterised SQL strings
│   │   └── helpers.py           # fetch_one / fetch_many / execute helpers
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── devices.py           # GET /devices, GET /devices/{id}, GET /devices/{id}/interfaces
│   │   ├── interfaces.py        # GET /interfaces/{id}, GET /interfaces/{id}/metrics
│   │   ├── telemetry.py         # POST /telemetry/ingest  (called by collector)
│   │   ├── alerts.py            # GET /alerts, PATCH /alerts/{id}/resolve
│   │   └── copilot.py           # POST /copilot/chat
│   │
│   ├── models/                  # Pydantic I/O schemas only (no ORM)
│   │   ├── __init__.py
│   │   ├── device.py
│   │   ├── interface.py
│   │   ├── metric.py
│   │   ├── alert.py
│   │   └── copilot.py
│   │
│   ├── scoring/                 # Dynamic ML risk-scoring engine
│   │   ├── __init__.py
│   │   ├── engine.py            # score_interface(metrics_window) → RiskScore
│   │   ├── formula.py           # Multi-factor weighted formula + Z-score baseline
│   │   └── detector.py          # Rolling-window anomaly detection → fires alert creation
│   │
│   ├── rag/                     # Full RAG pipeline skeleton (LLM stub)
│   │   ├── __init__.py
│   │   ├── context.py           # Retriever: pulls recent metrics + alerts from DB
│   │   ├── prompt.py            # Prompt builder (versioned templates)
│   │   ├── vector_store.py      # In-process vector store abstraction (stub → swap for pgvector/Chroma)
│   │   └── llm.py               # LLM client abstraction (mock | openai | ollama)
│   │
│   └── core/
│       ├── __init__.py
│       ├── errors.py            # Typed exceptions → HTTP responses
│       └── logging.py           # Structured JSON logging
│
├── alembic/                     # Alembic migrations (SQL DDL already in database/)
│   ├── env.py
│   ├── alembic.ini
│   └── versions/
│       └── 0001_initial.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # In-memory SQLite / fake pool fixtures
│   ├── test_scoring.py
│   ├── test_telemetry.py
│   └── test_devices.py
│
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
└── README.md
```

## Risk Scoring Formula

### Variables (from interface_metrics + interfaces)
- rx_bps, tx_bps = bytes / interval_seconds
- capacity_bps = interfaces.speed_bps
- utilization = (rx_bps + tx_bps) / (2 * capacity_bps)   [0..1]
- drop_rate = packet_drops / max(rx_packets_est, 1)       [derived]
- error_rate = errors / max(rx_bytes + tx_bytes, 1)       [0..1]
- trend = slope of rx_bps over last N samples             [delta/s]

### Weights
- W_util  = 0.30
- W_drop  = 0.40  (most impactful for packet loss)
- W_error = 0.20
- W_trend = 0.10

### Impact Score (0..1)
impact = clamp(W_util * utilization + W_drop * drop_rate_norm + W_error * error_rate_norm + W_trend * trend_norm)

### Z-score Baseline
baseline_z = (current_metric - rolling_mean) / rolling_std   [per interface, per metric]
anomaly_flag = any(|z| > sigma_threshold)  [default σ=3]

### Final Risk Score
severity_score = impact * (1 + 0.5 * clamp(max_z / sigma_threshold))
→ LOW < 0.30, MEDIUM 0.30..0.60, HIGH 0.60..0.80, CRITICAL >= 0.80

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/devices | List all devices |
| GET | /api/v1/devices/{id} | Device detail |
| GET | /api/v1/devices/{id}/interfaces | Interfaces for a device |
| GET | /api/v1/interfaces/{id} | Interface detail |
| GET | /api/v1/interfaces/{id}/metrics | Time-series metrics (query: from, to, limit) |
| GET | /api/v1/interfaces/{id}/score | Live risk score for interface |
| POST | /api/v1/telemetry/ingest | Ingest metric batch (called by collector) |
| GET | /api/v1/alerts | List alerts (filter: resolved, severity, device_id) |
| PATCH | /api/v1/alerts/{id}/resolve | Mark alert resolved |
| POST | /api/v1/copilot/chat | AI Copilot message |
| GET | /api/v1/health | Service health check |

## Key Design Decisions
1. NO SQLAlchemy ORM — only raw aiomysql with named parametrised queries in queries.py
2. Pool created once in lifespan, injected via app.state.pool
3. Scoring engine is pure Python math — no scikit-learn dependency yet
4. RAG context retriever queries the same MySQL pool — no separate vector DB needed for Phase 1
5. docker-compose.yml manages MySQL 8.0 container

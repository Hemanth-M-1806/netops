# NetOps Collection Layer

A standalone FastAPI microservice that sits between data sources and the backend database.

## Why it exists

- **Development**: Simulator pushes fake telemetry here instead of directly to backend
- **Production**: Replace simulator with real SNMP/gNMI collectors — only this service changes
- **Decoupling**: Backend never knows if data came from a simulator or real hardware

## Architecture

`
Simulator ----> POST /ingest -> CollectorService -> Forwarder ----> Backend
(or SNMP/gNMI)    sources/ (pluggable)   forwarders/ (pluggable)
`

## Quick start

`ash
cd collector
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
python -m app          # http://localhost:8100
COLLECTOR_FORWARDER=log python -m app   # dry-run
python -m pytest
`

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | /ingest | Accept telemetry batch |
| GET | /health | Liveness + config summary |
| GET | /metrics | Counters (received/accepted/failures) |
| GET | /docs | Swagger UI |

## Key env vars (COLLECTOR_* prefix)

- COLLECTOR_PORT=8100
- COLLECTOR_SOURCES=push  (comma-separated; add snmp,gnmi in prod)
- COLLECTOR_FORWARDER=backend
- COLLECTOR_FORWARD_URL=http://localhost:8000/api/v1/telemetry/ingest
- COLLECTOR_DRY_RUN=false
- COLLECTOR_API_KEY=  (empty = no auth)

## Extending

Add a new source: subclass BaseSource in app/sources/, register in registry.py
Add a new forwarder: subclass BaseForwarder in app/forwarders/, register in registry.py

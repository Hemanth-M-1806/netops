# NetOps Frontend — 3D Network Operations Center & AI Copilot

Modern, production-grade 3D Network Operations Center (NOC) dashboard built with React 18, TypeScript, Three.js / React Three Fiber, Tailwind CSS, TanStack Query, and Zustand.

---

## Features

- **3D Network Topology Visualizer (`/topology`)**:
  - WebGL / Three.js interactive 3D graph powered by `@react-three/fiber` and `@react-three/drei`.
  - Color-coded hardware models (Routers, Switches, Firewalls, Access Points).
  - Dynamic packet-pulse animations across network interconnections.
  - Interactive device drawer displaying telemetry health, interfaces, and active alarms.
- **Operations Command Center (`/`)**:
  - Real-time KPI metric cards (Active alerts, monitored devices, SLA status, telemetry ingest rate).
  - Embedded 3D topology preview card.
  - Live RX/TX interface throughput graphs powered by Recharts.
  - Active critical alerts feed.
- **Device Inventory (`/devices`)**:
  - Searchable, filterable hardware inventory with IP addresses, interface counts, and statuses.
  - Deep links to inspect devices in 3D or launch Copilot diagnostics.
- **Alert Triage Center (`/alerts`)**:
  - Filter by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and status (Active vs. Resolved).
  - One-click alert resolution updating the backend database in real time.
- **AI Copilot Terminal (`/copilot`)**:
  - Grounded RAG chat assistant answering natural language questions based on real-time MySQL telemetry and topology.
  - Device context scope selector with suggested diagnostic prompts.
- **NOC Settings (`/settings`)**:
  - Microservice connectivity beacons for Backend (:8000), MySQL (:3306), and Collector (:8100).

---

## Local Development

### Prerequisites
- Node.js 18+ or 20+
- NetOps Backend running on `http://127.0.0.1:8000`

### Installation & Run

```bash
# 1. Install dependencies
npm install

# 2. Start Vite development server with API proxy
npm run dev
```

The application will be accessible at: `http://localhost:5173`

---

## Production Build

```bash
# Run type check
npm run typecheck

# Build optimized production bundle
npm run build

# Preview build locally
npm run preview
```

---

## Docker Deployment

Build and run the standalone container with Nginx:

```bash
# Build Docker image
docker build -t netops-frontend -f Dockerfile .

# Run container on port 3000
docker run -d --name netops-frontend -p 3000:80 netops-frontend
```

Or run via `docker-compose.yml` from the repository root:

```bash
docker compose up --build frontend
```

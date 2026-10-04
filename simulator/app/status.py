"""Browsable status endpoint for the simulator.

The simulator is a fire-and-forget job (it has no API of its own), which makes
it hard to see what it is doing once it runs inside Docker.  While a run is
active this module serves a tiny HTTP endpoint from a daemon thread:

    GET /        -> human readable HTML dashboard (auto-refreshes every 5s)
    GET /status  -> JSON snapshot of the live counters
    GET /health  -> JSON liveness probe (used by the Docker healthcheck)

Deliberately stdlib-only (``http.server``) so the simulator's dependency list
stays minimal and the unit tests never need a web framework.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from app import __version__
from app.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Live run state published by app.runner and read by the request handlers.
_STATE: dict[str, Any] = {
    "settings": None,
    "scenario": None,
    "started_at": None,
    "simulator": None,
}

_SERVER: ThreadingHTTPServer | None = None
_THREAD: threading.Thread | None = None

# Registered by app.runner so POST /scenario can hot-swap the live scenario.
_SCENARIO_HOLDER: dict[str, Any] | None = None

# Coarse classification used to colour the fault-injection buttons.
_SCENARIO_KINDS = {
    "normal": "healthy",
    "mixed": "mixed",
    "high_traffic": "stress",
    "spikes": "stress",
    "packet_drops": "fault",
    "errors": "fault",
    "interface_failure": "fault",
    "device_failure": "critical",
}


def set_scenario_holder(holder: dict[str, Any]) -> None:
    """Register the runner's mutable scenario holder (enables hot-swapping)."""
    global _SCENARIO_HOLDER
    _SCENARIO_HOLDER = holder


def list_scenarios() -> list[dict[str, Any]]:
    """Scenario catalog for the dashboard (lazy import keeps startup light)."""
    from app.scenarios.catalog import SCENARIO_FACTORIES  # noqa: PLC0415

    current = _STATE.get("scenario")
    return [
        {
            "name": name,
            "description": factory().description,
            "kind": _SCENARIO_KINDS.get(name, "fault"),
            "active": name == current,
        }
        for name, factory in SCENARIO_FACTORIES.items()
    ]


def switch_scenario(name: str) -> dict[str, Any]:
    """Swap the live scenario (called by the dashboard's fault buttons)."""
    from app.scenarios.catalog import SCENARIO_FACTORIES  # noqa: PLC0415

    if name not in SCENARIO_FACTORIES:
        raise KeyError(name)
    if _SCENARIO_HOLDER is None:
        raise RuntimeError("no active run")

    # Build + reset first so the swap is a single atomic dict assignment.
    scenario = SCENARIO_FACTORIES[name]()
    scenario.reset()
    _SCENARIO_HOLDER["scenario"] = scenario
    _STATE["scenario"] = scenario.name
    # Start from healthy conditions and force a full status re-report so the
    # NOC dashboard recovers (devices/interfaces flip back to UP) on swap.
    simulator = _STATE.get("simulator")
    reset_conditions = getattr(simulator, "reset_conditions", None)
    if callable(reset_conditions):
        reset_conditions()
    logger.info("scenario.switched", extra={"stage": "status", "scenario": name})
    return {"name": scenario.name, "description": scenario.description}


def start(settings: Settings, scenario: str) -> None:
    """Start the status server (no-op when disabled or already running)."""
    global _SERVER, _THREAD
    if not settings.status_enabled:
        return
    if _SERVER is not None:
        return

    _STATE.update(
        settings=settings,
        scenario=scenario,
        started_at=datetime.now(tz=timezone.utc).isoformat(timespec="seconds"),
        simulator=None,
    )
    try:
        server = ThreadingHTTPServer((settings.host, settings.port), _StatusHandler)
    except OSError as exc:
        # Never let status reporting break the actual simulation run.
        logger.error(
            "status.start_failed",
            extra={"stage": "status", "port": settings.port, "error": str(exc)},
        )
        return

    _SERVER = server
    _THREAD = threading.Thread(
        target=server.serve_forever,
        name="simulator-status",
        daemon=True,
    )
    _THREAD.start()
    logger.info("status.started", extra={"stage": "status", "port": settings.port})


def set_simulator(simulator: Any) -> None:
    """Publish the live engine instance so endpoints can read its totals."""
    _STATE["simulator"] = simulator


def stop() -> None:
    """Stop the status server if it is running (safe to call repeatedly)."""
    global _SERVER, _THREAD
    server, _SERVER = _SERVER, None
    _THREAD = None
    _STATE["simulator"] = None
    if server is not None:
        server.shutdown()
        server.server_close()
        logger.info("status.stopped", extra={"stage": "status"})


def snapshot() -> dict[str, Any]:
    """Live counters + targets, shared by the HTML and JSON endpoints."""
    settings: Settings | None = _STATE["settings"]
    simulator = _STATE["simulator"]
    totals = dict(getattr(simulator, "totals", None) or {})
    return {
        "service": "netops-simulator",
        "version": __version__,
        # "starting" = discovery/registration phase, "running" = ticking.
        "status": "running" if simulator is not None else "starting",
        "scenario": _STATE["scenario"],
        "started_at": _STATE["started_at"],
        "totals": {
            "ticks": totals.get("ticks", 0),
            "samples": totals.get("samples", 0),
            "accepted": totals.get("accepted", 0),
            "failures": totals.get("failures", 0),
        },
        "interval_seconds": settings.interval_seconds if settings else None,
        "targets": {
            "backend": settings.api_base_url if settings else None,
            "collector": settings.collector_url if settings else None,
        },
        "links": {"self": "/", "status": "/status", "health": "/health"},
    }


def _render_html(data: dict[str, Any]) -> str:
    totals = data["totals"]
    targets = data["targets"]
    failures = int(totals.get("failures", 0))
    cards = "".join(
        f'<div class="card"><div class="k">{escape(str(key))}</div>'
        f'<div class="v{" bad" if key == "failures" and failures else ""}">'
        f"{value}</div></div>"
        for key, value in totals.items()
    )
    target_rows = "".join(
        f"<tr><td>{escape(str(key))}</td><td>{escape(str(value))}</td></tr>"
        for key, value in targets.items()
    )
    buttons = "".join(
        f'<button class="btn {s["kind"]}{" active" if s["active"] else ""}" '
        f'data-s="{escape(s["name"])}" title="{escape(s["description"])}" '
        f'onclick="inject(this)">'
        f'<b>{escape(s["name"])}</b><span>{escape(s["description"])}</span></button>'
        for s in list_scenarios()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="5">
<title>NetOps Simulator — Status</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; background:#0b1220; color:#cbd5e1;
         font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
  main {{ max-width:860px; margin:0 auto; padding:32px 20px; }}
  h1 {{ font-size:18px; color:#e2e8f0; letter-spacing:.06em; margin:0 0 4px; }}
  h2 {{ font-size:13px; color:#64748b; text-transform:uppercase;
        letter-spacing:.1em; margin:24px 0 8px; }}
  .badge {{ display:inline-block; padding:2px 10px; border-radius:999px;
            font-size:11px; background:#064e3b; color:#34d399; margin-left:8px; }}
  .muted {{ color:#64748b; font-size:12px; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
            gap:12px; margin:18px 0; }}
  .card {{ background:#111a2e; border:1px solid rgba(255,255,255,.08);
           border-radius:10px; padding:14px; }}
  .card .v {{ font-size:26px; color:#22d3ee; }}
  .card .v.bad {{ color:#f87171; }}
  .card .k {{ font-size:11px; color:#64748b; text-transform:uppercase;
              letter-spacing:.08em; }}
  table {{ width:100%; border-collapse:collapse; background:#111a2e;
           border:1px solid rgba(255,255,255,.08); border-radius:10px; }}
  th,td {{ padding:8px 12px; border-bottom:1px solid rgba(255,255,255,.06);
           text-align:left; font-size:13px; word-break:break-all; }}
  th {{ color:#64748b; font-size:11px; text-transform:uppercase;
        letter-spacing:.08em; }}
  a {{ color:#38bdf8; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
           gap:10px; }}
  .btn {{ display:flex; flex-direction:column; gap:4px; text-align:left;
          padding:12px 14px; border-radius:10px; background:#111a2e;
          border:1px solid rgba(255,255,255,.08); color:#cbd5e1;
          cursor:pointer; font:inherit; transition:border-color .15s; }}
  .btn:hover {{ border-color:rgba(56,189,248,.55); }}
  .btn b {{ font-size:13px; color:#e2e8f0; letter-spacing:.03em; }}
  .btn span {{ font-size:11px; color:#64748b; line-height:1.35; }}
  .btn.active {{ outline:2px solid #22d3ee; outline-offset:-2px; }}
  .btn.healthy b {{ color:#34d399; }}
  .btn.stress b {{ color:#fbbf24; }}
  .btn.fault b {{ color:#fb923c; }}
  .btn.mixed b {{ color:#22d3ee; }}
  .btn.critical b {{ color:#f87171; }}
  .btn.critical {{ animation:pulse 2s infinite; }}
  @keyframes pulse {{
    0%,100% {{ border-color:rgba(248,113,113,.25); }}
    50% {{ border-color:rgba(248,113,113,.85); }}
  }}
  .result {{ margin-top:10px; font-size:12px; min-height:16px; }}
  .result.ok {{ color:#34d399; }}
  .result.err {{ color:#f87171; }}
  .result.busy {{ color:#fbbf24; }}
</style>
</head>
<body><main>
  <h1>NETOPS SIMULATOR<span class="badge">{escape(str(data["status"]))}</span></h1>
  <p class="muted">scenario: <strong>{escape(str(data["scenario"]))}</strong>
     &middot; started: {escape(str(data["started_at"]))}
     &middot; interval: {escape(str(data["interval_seconds"]))}s
     &middot; auto-refresh 5s</p>
  <div class="cards">{cards}</div>
  <h2>Targets</h2>
  <table><tr><th>Service</th><th>URL</th></tr>{target_rows}</table>
  <h2>Fault Injection</h2>
  <p class="muted">Switch the live scenario — applies from the next tick
     (≈{escape(str(data["interval_seconds"]))}s). The <em>critical</em> options
     make the NOC dashboard (localhost:3000) show a real system failure:
     devices flip to DOWN and <code>interface_down</code> alerts fire.</p>
  <div class="grid">{buttons}</div>
  <div id="inject-result" class="result"></div>
  <p class="muted">JSON: <a href="/status">/status</a>
     &middot; <a href="/scenarios">/scenarios</a>
     &middot; <a href="/health">/health</a></p>
</main>
<script>
async function inject(btn) {{
  const el = document.getElementById('inject-result');
  el.className = 'result busy';
  el.textContent = '→ switching to ' + btn.dataset.s + ' …';
  try {{
    const r = await fetch('/scenario', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ name: btn.dataset.s }})
    }});
    const d = await r.json();
    if (r.ok) {{
      el.className = 'result ok';
      el.textContent = '✔ scenario "' + d.scenario + '" active — takes effect from the next tick.';
    }} else {{
      el.className = 'result err';
      el.textContent = '✖ ' + (d.detail || 'switch failed');
    }}
  }} catch (e) {{
    el.className = 'result err';
    el.textContent = '✖ ' + e;
  }}
}}
</script>
</body>
</html>
"""


class _StatusHandler(BaseHTTPRequestHandler):
    """Routes: / (HTML), /status (JSON), /health (JSON), everything else 404."""

    server_version = f"NetOpsSimulator/{__version__}"

    def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/":
            self._send(200, "text/html; charset=utf-8", _render_html(snapshot()))
        elif path == "/status":
            self._send_json(200, snapshot())
        elif path == "/scenarios":
            self._send_json(200, {"current": _STATE.get("scenario"), "items": list_scenarios()})
        elif path == "/health":
            data = snapshot()
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": data["service"],
                    "version": data["version"],
                },
            )
        else:
            self._send_json(404, {"detail": "Not Found"})

    def do_POST(self) -> None:  # noqa: N802 - fault-injection control plane
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path != "/scenario":
            self._send_json(404, {"detail": "Not Found"})
            return

        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            name = body.get("name")
        except (ValueError, json.JSONDecodeError):
            self._send_json(400, {"detail": "invalid JSON body"})
            return

        try:
            result = switch_scenario(str(name))
        except KeyError:
            from app.scenarios.catalog import SCENARIO_FACTORIES  # noqa: PLC0415

            self._send_json(
                400,
                {
                    "detail": f"unknown scenario '{name}'",
                    "available": sorted(SCENARIO_FACTORIES),
                },
            )
            return
        except RuntimeError:
            self._send_json(409, {"detail": "no active run — simulator is not running"})
            return

        self._send_json(
            200,
            {"ok": True, "scenario": result["name"], "description": result["description"]},
        )

    def _send_json(self, code: int, payload: dict[str, Any]) -> None:
        self._send(code, "application/json; charset=utf-8", json.dumps(payload))

    def _send(self, code: int, content_type: str, body: str) -> None:
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Route the default stderr access log through the app logger.
        logger.debug("status.request " + (fmt % args), extra={"stage": "status"})




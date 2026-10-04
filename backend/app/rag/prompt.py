"""
Versioned prompt templates.

Each version is a function (prompt_v1, prompt_v2, …).
The prompt builder selects the right version from Settings.prompt_version.
"""
from __future__ import annotations

from app.rag.context import RetrievedContext


def build_prompt(version: str, context: RetrievedContext, user_message: str) -> list[dict]:
    """
    Return an OpenAI-style messages list:
        [{"role": "system", ...}, {"role": "user", ...}]
    """
    builders = {"v1": _v1}
    fn = builders.get(version, _v1)
    return fn(context, user_message)


# ── v1 ────────────────────────────────────────────────────────────────────────

def _v1(context: RetrievedContext, user_message: str) -> list[dict]:
    system = _system_v1(context)
    return [
        {"role": "system", "content": system},
        {"role": "user",   "content": user_message},
    ]


def _system_v1(ctx: RetrievedContext) -> str:
    parts: list[str] = [
        "You are NetOps Copilot, an expert network operations AI assistant.",
        "Answer concisely and ground your analysis in the telemetry data below.",
        "",
    ]

    if ctx.device:
        d = ctx.device
        parts.append(
            f"## Device\n"
            f"Hostname: {d['hostname']}  |  IP: {d['ip_address']}  "
            f"|  Type: {d['device_type']}  |  Status: {d['status']}"
        )

    if ctx.interface:
        i = ctx.interface
        parts.append(
            f"## Interface\n"
            f"Name: {i['name']}  |  Type: {i['interface_type']}  "
            f"|  Status: {i['status']}  |  Speed: {_fmt_speed(i.get('speed_bps'))}"
        )

    if ctx.metrics:
        parts.append("## Recent Telemetry (newest first)")
        for m in ctx.metrics[:10]:
            parts.append(
                f"  {m['measured_at']}  "
                f"rx={_fmt_bytes(m['rx_bytes'])}  tx={_fmt_bytes(m['tx_bytes'])}  "
                f"drops={m['packet_drops']}  errors={m['errors']}"
            )

    if ctx.alerts:
        parts.append("## Active Alerts")
        for a in ctx.alerts:
            tag = "[OPEN]" if not a["resolved"] else "[resolved]"
            parts.append(
                f"  {tag} [{a['severity']}] {a['alert_type']}: {a['message']}"
            )

    parts.append(
        "\nIf you do not have enough data, say so. "
        "Do not invent metric values that are not shown above."
    )

    return "\n".join(parts)


# ── formatters ────────────────────────────────────────────────────────────────

def _fmt_bytes(b: int | None) -> str:
    if b is None:
        return "n/a"
    for unit, threshold in (("GB", 1e9), ("MB", 1e6), ("KB", 1e3)):
        if b >= threshold:
            return f"{b/threshold:.1f}{unit}"
    return f"{b}B"


def _fmt_speed(bps: int | None) -> str:
    if bps is None:
        return "unknown"
    if bps >= 1e9:
        return f"{bps/1e9:.0f} Gbps"
    if bps >= 1e6:
        return f"{bps/1e6:.0f} Mbps"
    return f"{bps} bps"

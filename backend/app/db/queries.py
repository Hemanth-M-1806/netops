"""
Named parameterised SQL queries.

All SQL lives here — nowhere else in the application.
Changing a query means editing this file only.

Convention: every constant is UPPER_SNAKE_CASE.
Args are passed as Python tuples/dicts via aiomysql's %(name)s syntax.
"""

# ── DEVICES ──────────────────────────────────────────────────────────────────

DEVICES_LIST = """
    SELECT id, hostname, ip_address, device_type, status,
           location, description, created_at, updated_at
    FROM   devices
    ORDER  BY hostname ASC
"""

DEVICES_LIST_FILTERED = """
    SELECT id, hostname, ip_address, device_type, status,
           location, description, created_at, updated_at
    FROM   devices
    WHERE  (%s IS NULL OR status = %s)
      AND  (%s IS NULL OR device_type = %s)
    ORDER  BY hostname ASC
    LIMIT  %s OFFSET %s
"""

DEVICES_COUNT = """
    SELECT COUNT(*) AS total FROM devices
    WHERE  (%s IS NULL OR status = %s)
      AND  (%s IS NULL OR device_type = %s)
"""

DEVICE_BY_ID = """
    SELECT id, hostname, ip_address, device_type, status,
           location, description, created_at, updated_at
    FROM   devices
    WHERE  id = %s
"""

DEVICE_BY_HOSTNAME = """
    SELECT id, hostname, ip_address, device_type, status,
           location, description, created_at, updated_at
    FROM   devices
    WHERE  hostname = %s
"""

DEVICE_UPDATE_STATUS = """
    UPDATE devices SET status = %s WHERE id = %s
"""

# ── INTERFACES ────────────────────────────────────────────────────────────────

INTERFACES_FOR_DEVICE = """
    SELECT id, device_id, name, interface_type, status,
           speed_bps, description, created_at, updated_at
    FROM   interfaces
    WHERE  device_id = %s
    ORDER  BY name ASC
"""

INTERFACE_BY_ID = """
    SELECT i.id, i.device_id, i.name, i.interface_type, i.status,
           i.speed_bps, i.description, i.created_at, i.updated_at,
           d.hostname
    FROM   interfaces i
    JOIN   devices d ON d.id = i.device_id
    WHERE  i.id = %s
"""

INTERFACE_BY_DEVICE_AND_NAME = """
    SELECT id, device_id, name, interface_type, status,
           speed_bps, description, created_at, updated_at
    FROM   interfaces
    WHERE  device_id = %s AND name = %s
"""

INTERFACE_UPDATE_STATUS = """
    UPDATE interfaces SET status = %s WHERE id = %s
"""

# ── INTERFACE_METRICS (time-series) ───────────────────────────────────────────

# Bulk insert — called by the telemetry ingest endpoint
METRICS_INSERT = """
    INSERT INTO interface_metrics
        (interface_id, rx_bytes, tx_bytes, packet_drops, errors, measured_at)
    VALUES
        (%s, %s, %s, %s, %s, %s)
"""

# Latest N samples for a given interface (for scoring window)
METRICS_LATEST = """
    SELECT id, interface_id, rx_bytes, tx_bytes, packet_drops,
           errors, measured_at, ingested_at
    FROM   interface_metrics
    WHERE  interface_id = %s
    ORDER  BY measured_at DESC
    LIMIT  %s
"""

# Time-range query (for dashboard charts)
METRICS_RANGE = """
    SELECT id, interface_id, rx_bytes, tx_bytes, packet_drops,
           errors, measured_at, ingested_at
    FROM   interface_metrics
    WHERE  interface_id = %s
      AND  measured_at BETWEEN %s AND %s
    ORDER  BY measured_at ASC
    LIMIT  %s
"""

# Per-interface aggregate stats (used by RAG context retriever)
METRICS_AGG = """
    SELECT
        interface_id,
        COUNT(*)                            AS sample_count,
        AVG(rx_bytes + tx_bytes)            AS avg_total_bytes,
        MAX(rx_bytes + tx_bytes)            AS max_total_bytes,
        AVG(packet_drops)                   AS avg_drops,
        MAX(packet_drops)                   AS max_drops,
        AVG(errors)                         AS avg_errors,
        MAX(errors)                         AS max_errors,
        MIN(measured_at)                    AS window_start,
        MAX(measured_at)                    AS window_end
    FROM   interface_metrics
    WHERE  interface_id = %s
      AND  measured_at >= NOW() - INTERVAL %s SECOND
    GROUP  BY interface_id
"""

# ── ALERTS ───────────────────────────────────────────────────────────────────

ALERTS_LIST = """
    SELECT a.id, a.interface_id, a.severity, a.alert_type, a.message,
           a.resolved, a.triggered_at, a.resolved_at,
           i.name  AS interface_name,
           d.hostname
    FROM   alerts a
    JOIN   interfaces i ON i.id = a.interface_id
    JOIN   devices    d ON d.id = i.device_id
    WHERE  (%s IS NULL OR a.resolved = %s)
      AND  (%s IS NULL OR a.severity = %s)
      AND  (%s IS NULL OR d.id = %s)
    ORDER  BY a.triggered_at DESC
    LIMIT  %s OFFSET %s
"""

ALERTS_COUNT = """
    SELECT COUNT(*) AS total
    FROM   alerts a
    JOIN   interfaces i ON i.id = a.interface_id
    JOIN   devices    d ON d.id = i.device_id
    WHERE  (%s IS NULL OR a.resolved = %s)
      AND  (%s IS NULL OR a.severity = %s)
      AND  (%s IS NULL OR d.id = %s)
"""

ALERT_BY_ID = """
    SELECT a.id, a.interface_id, a.severity, a.alert_type, a.message,
           a.resolved, a.triggered_at, a.resolved_at,
           i.name AS interface_name, d.hostname
    FROM   alerts a
    JOIN   interfaces i ON i.id = a.interface_id
    JOIN   devices    d ON d.id = i.device_id
    WHERE  a.id = %s
"""

ALERT_INSERT = """
    INSERT INTO alerts (interface_id, severity, alert_type, message)
    VALUES (%s, %s, %s, %s)
"""

ALERT_RESOLVE = """
    UPDATE alerts
    SET    resolved = 1, resolved_at = NOW(6)
    WHERE  id = %s
"""

# Recent unresolved alerts for a given interface (used by detector de-dup)
ALERT_RECENT_UNRESOLVED = """
    SELECT id, alert_type, triggered_at
    FROM   alerts
    WHERE  interface_id = %s
      AND  resolved = 0
      AND  alert_type = %s
      AND  triggered_at >= NOW() - INTERVAL 300 SECOND
    LIMIT  1
"""

# Auto-resolve every open alert of a type (used when an interface recovers)
ALERT_RESOLVE_BY_TYPE = """
    UPDATE alerts
    SET    resolved = 1, resolved_at = NOW(6)
    WHERE  interface_id = %s
      AND  alert_type = %s
      AND  resolved = 0
"""

# ── CHAT_MESSAGES ─────────────────────────────────────────────────────────────

CHAT_INSERT = """
    INSERT INTO chat_messages (session_id, role, content, token_count)
    VALUES (%s, %s, %s, %s)
"""

CHAT_HISTORY = """
    SELECT id, session_id, role, content, token_count, created_at
    FROM   chat_messages
    WHERE  session_id = %s
    ORDER  BY created_at ASC
    LIMIT  %s
"""

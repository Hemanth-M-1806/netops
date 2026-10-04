-- ============================================================
-- Migration 0001 — initial schema
-- Equivalent to schema/schema.sql, tracked by Alembic.
-- ============================================================

-- UP
CREATE TABLE IF NOT EXISTS devices (
    id            INT UNSIGNED    NOT NULL AUTO_INCREMENT,
    hostname      VARCHAR(128)    NOT NULL,
    ip_address    VARCHAR(45)     NOT NULL,
    device_type   ENUM('router','switch','firewall','loadbalancer','access_point','other') NOT NULL DEFAULT 'other',
    status        ENUM('UP','DOWN','WARNING','CRITICAL','MAINTENANCE','UNKNOWN') NOT NULL DEFAULT 'UNKNOWN',
    location      VARCHAR(256)    DEFAULT NULL,
    description   TEXT            DEFAULT NULL,
    created_at    DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at    DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_devices_hostname   (hostname),
    UNIQUE KEY uq_devices_ip_address (ip_address),
    INDEX idx_devices_status (status),
    INDEX idx_devices_type   (device_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS interfaces (
    id               INT UNSIGNED NOT NULL AUTO_INCREMENT,
    device_id        INT UNSIGNED NOT NULL,
    name             VARCHAR(64)  NOT NULL,
    interface_type   ENUM('ethernet','loopback','vlan','tunnel','other') NOT NULL DEFAULT 'ethernet',
    status           ENUM('UP','DOWN','ADMIN_DOWN','ERROR','UNKNOWN')    NOT NULL DEFAULT 'UNKNOWN',
    speed_bps        BIGINT UNSIGNED DEFAULT NULL,
    description      VARCHAR(256) DEFAULT NULL,
    created_at       DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at       DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uq_interfaces_device_name (device_id, name),
    INDEX idx_interfaces_device_id (device_id),
    INDEX idx_interfaces_status    (status),
    CONSTRAINT fk_interfaces_device FOREIGN KEY (device_id) REFERENCES devices (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS interface_metrics (
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    interface_id  INT UNSIGNED    NOT NULL,
    rx_bytes      BIGINT UNSIGNED NOT NULL DEFAULT 0,
    tx_bytes      BIGINT UNSIGNED NOT NULL DEFAULT 0,
    packet_drops  INT UNSIGNED    NOT NULL DEFAULT 0,
    errors        INT UNSIGNED    NOT NULL DEFAULT 0,
    measured_at   DATETIME(6)     NOT NULL,
    ingested_at   DATETIME(6)     NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_metrics_interface_time (interface_id, measured_at DESC),
    INDEX idx_metrics_measured_at    (measured_at DESC),
    CONSTRAINT fk_metrics_interface FOREIGN KEY (interface_id) REFERENCES interfaces (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS alerts (
    id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
    interface_id INT UNSIGNED NOT NULL,
    severity     ENUM('LOW','MEDIUM','HIGH','CRITICAL') NOT NULL DEFAULT 'LOW',
    alert_type   VARCHAR(64)  NOT NULL,
    message      TEXT         NOT NULL,
    resolved     TINYINT(1)   NOT NULL DEFAULT 0,
    triggered_at DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    resolved_at  DATETIME(6)  DEFAULT NULL,
    PRIMARY KEY (id),
    INDEX idx_alerts_interface (interface_id),
    INDEX idx_alerts_severity  (severity),
    INDEX idx_alerts_resolved  (resolved),
    INDEX idx_alerts_triggered (triggered_at DESC),
    CONSTRAINT fk_alerts_interface FOREIGN KEY (interface_id) REFERENCES interfaces (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    session_id  VARCHAR(36)  NOT NULL,
    role        ENUM('user','assistant','system') NOT NULL,
    content     TEXT         NOT NULL,
    token_count INT UNSIGNED DEFAULT NULL,
    created_at  DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    INDEX idx_chat_session (session_id, created_at ASC),
    INDEX idx_chat_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

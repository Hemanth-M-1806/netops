-- ============================================================
-- Alembic env.py bootstrap SQL
-- Run this ONCE to let Alembic track its own version table.
-- After this, use: alembic upgrade head
-- ============================================================

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

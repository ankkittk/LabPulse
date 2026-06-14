-- ============================================================
-- LabPulse Database Schema
-- ============================================================
-- Run once against a MySQL server to initialise the database.
-- Usage: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS labpulse
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE labpulse;

-- ------------------------------------------------------------
-- computers
-- One row per physical PC registered in the lab.
-- The pc_name (hostname) is the natural unique identifier.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS computers (
    id          INT          NOT NULL AUTO_INCREMENT,
    pc_name     VARCHAR(100) NOT NULL,          -- e.g. "LAB-PC-01"
    ip_address  VARCHAR(45),                    -- supports IPv6 too
    last_seen   DATETIME,                       -- updated on every agent heartbeat
    status      VARCHAR(20)  NOT NULL DEFAULT 'offline',  -- 'online' | 'offline'

    PRIMARY KEY (id),
    UNIQUE KEY uq_pc_name (pc_name)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- resource_snapshots
-- Time-series table — one row per agent heartbeat (~every 10s).
-- Grows continuously; consider partitioning by month in future.
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resource_snapshots (
    id           INT          NOT NULL AUTO_INCREMENT,
    computer_id  INT          NOT NULL,
    cpu_usage    FLOAT,           -- percentage 0–100
    ram_usage    FLOAT,           -- percentage 0–100
    disk_usage   FLOAT,           -- percentage 0–100
    timestamp    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_computer_timestamp (computer_id, timestamp),   -- optimises history queries
    CONSTRAINT fk_snapshot_computer FOREIGN KEY (computer_id)
        REFERENCES computers (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- alerts
-- Logged whenever a resource reading breaches a threshold.
-- alert_type: 'HIGH_CPU' | 'HIGH_RAM' | 'HIGH_DISK' | 'OFFLINE'
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id           INT          NOT NULL AUTO_INCREMENT,
    computer_id  INT          NOT NULL,
    alert_type   VARCHAR(50)  NOT NULL,
    message      TEXT,
    timestamp    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    KEY idx_alert_computer (computer_id),
    CONSTRAINT fk_alert_computer FOREIGN KEY (computer_id)
        REFERENCES computers (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- Sample seed data for development / demo purposes
-- Remove this block before presenting in a live environment.
-- ============================================================
INSERT IGNORE INTO computers (pc_name, ip_address, last_seen, status) VALUES
    ('LAB-PC-01', '192.168.1.101', NOW(), 'offline'),
    ('LAB-PC-02', '192.168.1.102', NOW(), 'offline'),
    ('LAB-PC-03', '192.168.1.103', NOW(), 'offline');

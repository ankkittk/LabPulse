-- ============================================================
-- LabPulse Database Schema v2
-- ============================================================

CREATE DATABASE IF NOT EXISTS labpulse
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE labpulse;

-- ------------------------------------------------------------
-- computers
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS computers (
    id          INT          NOT NULL AUTO_INCREMENT,
    pc_name     VARCHAR(100) NOT NULL,
    ip_address  VARCHAR(45),
    last_seen   DATETIME,
    status      VARCHAR(20)  NOT NULL DEFAULT 'offline',
    PRIMARY KEY (id),
    UNIQUE KEY uq_pc_name (pc_name)
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- resource_snapshots
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS resource_snapshots (
    id                INT          NOT NULL AUTO_INCREMENT,
    computer_id       INT          NOT NULL,
    cpu_usage         FLOAT,
    ram_usage         FLOAT,
    disk_usage        FLOAT,
    network_sent      BIGINT UNSIGNED,
    network_recv      BIGINT UNSIGNED,
    boot_time         BIGINT UNSIGNED,
    process_count     INT UNSIGNED,
    top_process_name  VARCHAR(255),
    top_process_cpu   FLOAT,
    top_process_memory FLOAT,
    timestamp         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_computer_timestamp (computer_id, timestamp),
    CONSTRAINT fk_snapshot_computer FOREIGN KEY (computer_id)
        REFERENCES computers (id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- alerts
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
-- Seed data for development
-- ============================================================
INSERT IGNORE INTO computers (pc_name, ip_address, last_seen, status) VALUES
    ('LAB-PC-01', '192.168.1.101', NOW(), 'offline'),
    ('LAB-PC-02', '192.168.1.102', NOW(), 'offline'),
    ('LAB-PC-03', '192.168.1.103', NOW(), 'offline');
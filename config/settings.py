"""
config/settings.py
==================

Single source of truth for all LabPulse configuration.

Values are read from environment variables first (so they can be overridden
at runtime without code changes), falling back to sensible defaults.

Usage:
    from config.settings import DB_HOST, TCP_PORT, ...

Academic note: Centralising configuration avoids scattering magic numbers
throughout the codebase. In a larger system this would use Pydantic's
BaseSettings for automatic type-casting and validation.
"""

import os
from dotenv import load_dotenv

# Load .env file if present (development convenience)
load_dotenv()


# ── MySQL ──────────────────────────────────────────────────────────────────────
DB_HOST:     str = os.getenv("DB_HOST", "localhost")
DB_PORT:     int = int(os.getenv("DB_PORT", "3306"))
DB_USER:     str = os.getenv("DB_USER", "root")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
DB_NAME:     str = os.getenv("DB_NAME", "labpulse")

# ── TCP Listener ───────────────────────────────────────────────────────────────
TCP_HOST:        str = os.getenv("TCP_HOST", "0.0.0.0")
TCP_PORT:        int = int(os.getenv("TCP_PORT", "9000"))
TCP_BUFFER_SIZE: int = 4096   # bytes per recv() call

# ── Agent ──────────────────────────────────────────────────────────────────────
AGENT_INTERVAL: int = int(os.getenv("AGENT_INTERVAL", "10"))  # seconds
SERVER_HOST:    str = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT:    int = int(os.getenv("SERVER_PORT", "9000"))

# ── Alert thresholds ───────────────────────────────────────────────────────────
CPU_ALERT_THRESHOLD:  float = float(os.getenv("CPU_ALERT_THRESHOLD", "85.0"))
RAM_ALERT_THRESHOLD:  float = float(os.getenv("RAM_ALERT_THRESHOLD", "85.0"))
DISK_ALERT_THRESHOLD: float = float(os.getenv("DISK_ALERT_THRESHOLD", "90.0"))

# ── Offline detection ──────────────────────────────────────────────────────────
OFFLINE_TIMEOUT_SECONDS: int = int(os.getenv("OFFLINE_TIMEOUT_SECONDS", "60"))

"""
server/database.py
==================

DatabaseManager encapsulates every MySQL operation in LabPulse.

Design decisions (explain these in an interview):
  • Connection pooling — a pool of 5 reusable connections avoids the overhead
    of opening a new TCP connection to MySQL for every request.
  • dictionary=True cursors — rows come back as dicts so the API layer does not
    need to know column positions.
  • ON DUPLICATE KEY UPDATE — upsert pattern keeps computer registration
    idempotent; the agent does not need a separate "register" step.
  • The class owns no long-lived connections; each public method borrows from
    the pool and returns it on exit. This is safe for concurrent callers.

Academic note (DBMS):
  The resource_snapshots table is a time-series table. The composite index on
  (computer_id, timestamp) is critical — without it, GET /history would do a
  full table scan as the table grows.
"""

import logging
from typing import Any, Dict, List

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool

from config.settings import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Single access point for all LabPulse database operations.

    Instantiated once at server startup (in server/main.py) and shared
    across the TCP listener thread and FastAPI request handlers.
    """

    # ── Construction ──────────────────────────────────────────────────────────

    def __init__(self) -> None:
        self._pool: MySQLConnectionPool = self._create_pool()

    def _create_pool(self) -> MySQLConnectionPool:
        """
        Create a pool of 5 persistent MySQL connections.
        Raises on misconfiguration so startup fails fast rather than at first query.
        """
        try:
            pool = MySQLConnectionPool(
                pool_name="labpulse_pool",
                pool_size=5,
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True,
                connection_timeout=10,
            )
            logger.info("MySQL connection pool initialised (size=5).")
            return pool
        except Error as exc:
            logger.critical(f"Failed to connect to MySQL: {exc}")
            raise

    def _get_conn(self):
        """Borrow a connection from the pool. Caller must call conn.close() to return it."""
        return self._pool.get_connection()

    # ── Computer operations ───────────────────────────────────────────────────

    def upsert_computer(self, pc_name: str, ip_address: str) -> int:
        """
        Register a computer if it is new; update last_seen + status if it exists.
        Returns the computer's primary key (used when inserting snapshots/alerts).

        Uses MySQL's INSERT … ON DUPLICATE KEY UPDATE for an atomic upsert.
        The UNIQUE constraint on pc_name makes this safe.
        """
        sql_upsert = """
            INSERT INTO computers (pc_name, ip_address, last_seen, status)
            VALUES (%s, %s, NOW(), 'online')
            ON DUPLICATE KEY UPDATE
                ip_address = VALUES(ip_address),
                last_seen  = NOW(),
                status     = 'online'
        """
        sql_select = "SELECT id FROM computers WHERE pc_name = %s"

        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql_upsert, (pc_name, ip_address))
            cursor.execute(sql_select, (pc_name,))
            row = cursor.fetchone()
            return row[0]
        except Error as exc:
            logger.error(f"upsert_computer({pc_name!r}) failed: {exc}")
            raise
        finally:
            cursor.close()
            conn.close()   # returns the connection to the pool

    def get_all_computers(self) -> List[Dict[str, Any]]:
        """Return every computer row, ordered alphabetically by name."""
        sql = """
            SELECT id, pc_name, ip_address, last_seen, status
            FROM computers
            ORDER BY pc_name
        """
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def mark_offline_computers(self, timeout_seconds: int) -> int:
        """
        Flip any computer to 'offline' that has not reported within timeout_seconds.

        Uses TIMESTAMPDIFF so the threshold can be parameterised safely without
        string formatting (which would open a SQL-injection risk).

        Returns the number of rows updated.

        # TODO: Call this from a background scheduler (e.g., APScheduler)
        #        every ~30 seconds so the dashboard stays accurate.
        """
        sql = """
            UPDATE computers
               SET status = 'offline'
             WHERE status = 'online'
               AND TIMESTAMPDIFF(SECOND, last_seen, NOW()) > %s
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (timeout_seconds,))
            affected = cursor.rowcount
            if affected:
                logger.info(f"Marked {affected} computer(s) as offline.")
            return affected
        except Error as exc:
            logger.error(f"mark_offline_computers failed: {exc}")
            return 0
        finally:
            cursor.close()
            conn.close()

    # ── Snapshot operations ───────────────────────────────────────────────────

    def insert_snapshot(
        self, computer_id: int, cpu: float, ram: float, disk: float
    ) -> None:
        """Write one resource reading to resource_snapshots."""
        sql = """
            INSERT INTO resource_snapshots
                        (computer_id, cpu_usage, ram_usage, disk_usage, timestamp)
            VALUES      (%s, %s, %s, %s, NOW())
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (computer_id, cpu, ram, disk))
        except Error as exc:
            logger.error(f"insert_snapshot(computer_id={computer_id}) failed: {exc}")
            raise
        finally:
            cursor.close()
            conn.close()

    def get_latest_status(self) -> List[Dict[str, Any]]:
        """
        Return the most recent snapshot for every computer in a single query.

        The correlated subquery finds the MAX id per computer — safe because
        AUTO_INCREMENT ids are monotonically increasing so the highest id is
        always the most recent row.

        Academic note: An alternative is a window function (ROW_NUMBER OVER …)
        which is more readable but requires MySQL 8+.
        """
        sql = """
            SELECT
                c.pc_name,
                c.ip_address,
                c.status,
                c.last_seen,
                rs.cpu_usage,
                rs.ram_usage,
                rs.disk_usage
            FROM computers c
            LEFT JOIN resource_snapshots rs
                   ON rs.id = (
                        SELECT id
                          FROM resource_snapshots
                         WHERE computer_id = c.id
                         ORDER BY id DESC
                         LIMIT 1
                      )
            ORDER BY c.pc_name
        """
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql)
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_history(self, pc_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Return the last `limit` snapshots for one computer, newest first.
        The dashboard reverses this to oldest-first for charting.
        """
        sql = """
            SELECT rs.id,
                   rs.computer_id,
                   rs.cpu_usage,
                   rs.ram_usage,
                   rs.disk_usage,
                   rs.timestamp
              FROM resource_snapshots rs
              JOIN computers c ON c.id = rs.computer_id
             WHERE c.pc_name = %s
             ORDER BY rs.timestamp DESC
             LIMIT %s
        """
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, (pc_name, limit))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    # ── Alert operations ──────────────────────────────────────────────────────

    def insert_alert(
        self, computer_id: int, alert_type: str, message: str
    ) -> None:
        """Persist one alert record. Called by AlertManager."""
        sql = """
            INSERT INTO alerts (computer_id, alert_type, message, timestamp)
            VALUES (%s, %s, %s, NOW())
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(sql, (computer_id, alert_type, message))
        except Error as exc:
            logger.error(f"insert_alert failed: {exc}")
        finally:
            cursor.close()
            conn.close()

    def get_recent_alerts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent `limit` alerts, joined with computer name."""
        sql = """
            SELECT a.id,
                   c.pc_name,
                   a.alert_type,
                   a.message,
                   a.timestamp
              FROM alerts a
              JOIN computers c ON c.id = a.computer_id
             ORDER BY a.timestamp DESC
             LIMIT %s
        """
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, (limit,))
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

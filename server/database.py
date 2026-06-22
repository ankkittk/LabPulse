"""
server/database.py
==================

Database access layer for LabPulse.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import mysql.connector
from mysql.connector import Error
from mysql.connector.pooling import MySQLConnectionPool

from config.settings import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
from server.analytics.health_score import assess_health

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self) -> None:
        self._pool: MySQLConnectionPool = self._create_pool()

    def _create_pool(self) -> MySQLConnectionPool:
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
        return self._pool.get_connection()

    def _enrich_snapshot(self, row: Dict[str, Any]) -> Dict[str, Any]:
        enriched = dict(row)
        if enriched.get("cpu_usage") is None:
            enriched["health_score"] = None
            enriched["health_status"] = None
            return enriched

        assessment = assess_health(
            cpu_usage=enriched.get("cpu_usage"),
            ram_usage=enriched.get("ram_usage"),
            disk_usage=enriched.get("disk_usage"),
            process_count=enriched.get("process_count"),
            top_process_cpu=enriched.get("top_process_cpu"),
            top_process_memory=enriched.get("top_process_memory"),
        )
        enriched["health_score"] = assessment.score
        enriched["health_status"] = assessment.status
        return enriched

    def upsert_computer(self, pc_name: str, ip_address: str) -> int:
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
            return int(row[0])
        except Error as exc:
            logger.error(f"upsert_computer({pc_name!r}) failed: {exc}")
            raise
        finally:
            cursor.close()
            conn.close()

    def get_all_computers(self) -> List[Dict[str, Any]]:
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

    def get_computer_by_name(self, pc_name: str) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT id, pc_name, ip_address, last_seen, status
            FROM computers
            WHERE pc_name = %s
            LIMIT 1
        """
        conn = self._get_conn()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, (pc_name,))
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def mark_offline_computers(self, timeout_seconds: int) -> int:
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

    def insert_snapshot(
        self,
        computer_id: int,
        cpu: float,
        ram: float,
        disk: float,
        network_sent: float = 0.0,
        network_recv: float = 0.0,
        boot_time: int = 0,
        process_count: int = 0,
        top_process_name: Optional[str] = None,
        top_process_cpu: float = 0.0,
        top_process_memory: float = 0.0,
    ) -> None:
        sql = """
            INSERT INTO resource_snapshots
                (computer_id, cpu_usage, ram_usage, disk_usage,
                 network_sent, network_recv, boot_time, process_count,
                 top_process_name, top_process_cpu, top_process_memory,
                 timestamp)
            VALUES
                (%s, %s, %s, %s,
                 %s, %s, %s, %s,
                 %s, %s, %s,
                 NOW())
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                sql,
                (
                    computer_id,
                    cpu,
                    ram,
                    disk,
                    int(network_sent),
                    int(network_recv),
                    int(boot_time),
                    int(process_count),
                    top_process_name,
                    float(top_process_cpu),
                    float(top_process_memory),
                ),
            )
        except Error as exc:
            logger.error(f"insert_snapshot(computer_id={computer_id}) failed: {exc}")
            raise
        finally:
            cursor.close()
            conn.close()

    def get_latest_status(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                c.pc_name,
                c.ip_address,
                c.status,
                c.last_seen,
                rs.cpu_usage,
                rs.ram_usage,
                rs.disk_usage,
                rs.network_sent,
                rs.network_recv,
                rs.boot_time,
                rs.process_count,
                rs.top_process_name,
                rs.top_process_cpu,
                rs.top_process_memory,
                rs.timestamp
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
            rows = cursor.fetchall()
            return [self._enrich_snapshot(row) for row in rows]
        finally:
            cursor.close()
            conn.close()

    def get_history(self, pc_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        sql = """
            SELECT rs.id,
                   rs.computer_id,
                   rs.cpu_usage,
                   rs.ram_usage,
                   rs.disk_usage,
                   rs.network_sent,
                   rs.network_recv,
                   rs.boot_time,
                   rs.process_count,
                   rs.top_process_name,
                   rs.top_process_cpu,
                   rs.top_process_memory,
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
            rows = cursor.fetchall()
            return [self._enrich_snapshot(row) for row in rows]
        finally:
            cursor.close()
            conn.close()

    def get_machine_details(self, pc_name: str, limit: int = 50) -> Optional[Dict[str, Any]]:
        computer = self.get_computer_by_name(pc_name)
        if not computer:
            return None

        history = self.get_history(pc_name, limit)
        latest_snapshot = history[0] if history else None

        return {
            "computer": computer,
            "latest_snapshot": latest_snapshot,
            "history": history,
        }

    def insert_alert(self, computer_id: int, alert_type: str, message: str) -> None:
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

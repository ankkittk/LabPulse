from __future__ import annotations

import threading
import time

from config.settings import OFFLINE_TIMEOUT_SECONDS
from server.alert_manager import AlertManager
from server.database import DatabaseManager
from server.tcp_listener import TCPListener


db = DatabaseManager()
alert_manager = AlertManager(db)


def process_agent_payload(payload: dict, client_ip: str) -> None:
    hostname = payload["hostname"]
    cpu = float(payload["cpu_usage"])
    ram = float(payload["ram_usage"])
    disk = float(payload["disk_usage"])

    network_sent = float(payload.get("network_sent", 0.0))
    network_recv = float(payload.get("network_recv", 0.0))
    boot_time = int(payload.get("boot_time", 0))
    process_count = int(payload.get("process_count", 0))
    top_process_name = payload.get("top_process_name")
    top_process_cpu = float(payload.get("top_process_cpu", 0.0))
    top_process_memory = float(payload.get("top_process_memory", 0.0))

    computer_id = db.upsert_computer(
        pc_name=hostname,
        ip_address=client_ip,
    )

    db.insert_snapshot(
        computer_id=computer_id,
        cpu=cpu,
        ram=ram,
        disk=disk,
        network_sent=network_sent,
        network_recv=network_recv,
        boot_time=boot_time,
        process_count=process_count,
        top_process_name=top_process_name,
        top_process_cpu=top_process_cpu,
        top_process_memory=top_process_memory,
    )

    alert_manager.evaluate(
        computer_id=computer_id,
        pc_name=hostname,
        cpu=cpu,
        ram=ram,
        disk=disk,
    )

    print(f"Stored snapshot from {hostname}")


def offline_maintenance_loop() -> None:
    while True:
        try:
            db.mark_offline_computers(OFFLINE_TIMEOUT_SECONDS)
        except Exception as exc:
            print(f"Offline maintenance error: {exc}")
        time.sleep(30)


listener = TCPListener(process_agent_payload)


if __name__ == "__main__":
    listener.start()
    threading.Thread(target=offline_maintenance_loop, daemon=True).start()

    print("LabPulse TCP Server Running...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
        print("LabPulse TCP Server stopped.")

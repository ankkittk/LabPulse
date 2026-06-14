from server.database import DatabaseManager
from server.alert_manager import AlertManager
from server.tcp_listener import TCPListener


db = DatabaseManager()
alert_manager = AlertManager(db)


def process_agent_payload(payload: dict, client_ip: str) -> None:
    hostname = payload["hostname"]
    cpu = payload["cpu_usage"]
    ram = payload["ram_usage"]
    disk = payload["disk_usage"]

    computer_id = db.upsert_computer(
        pc_name=hostname,
        ip_address=client_ip
    )

    db.insert_snapshot(
        computer_id=computer_id,
        cpu=cpu,
        ram=ram,
        disk=disk
    )

    alert_manager.evaluate(
        computer_id=computer_id,
        pc_name=hostname,
        cpu=cpu,
        ram=ram,
        disk=disk
    )

    print(f"Stored snapshot from {hostname}")


listener = TCPListener(process_agent_payload)
listener.start()

print("LabPulse TCP Server Running...")

input()

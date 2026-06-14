import time

from agent.collector import SystemCollector
from agent.sender import TCPSender
from config.settings import AGENT_INTERVAL


class MonitoringAgent:
    def __init__(self) -> None:
        self.collector = SystemCollector()
        self.sender = TCPSender()

    def run_once(self) -> None:
        snapshot = self.collector.collect()
        payload = snapshot.to_dict()
        print(payload)
        self.sender.send(payload)

    def run_forever(self) -> None:
        while True:
            try:
                self.run_once()
            except Exception as exc:
                print(f"Agent error: {exc}")
            time.sleep(AGENT_INTERVAL)


if __name__ == "__main__":
    MonitoringAgent().run_forever()

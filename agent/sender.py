import json
import socket
from typing import Dict, Any

from config.settings import SERVER_HOST, SERVER_PORT


class TCPSender:
    def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT) -> None:
        self.host = host
        self.port = port

    def send(self, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload).encode("utf-8")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((self.host, self.port))
            sock.sendall(data)
            try:
                sock.shutdown(socket.SHUT_WR)
            except OSError:
                pass

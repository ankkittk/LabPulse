"""
server/tcp_listener.py
======================

TCPListener — a multi-threaded TCP server that accepts connections from
monitoring agents running on lab PCs.

Protocol (deliberately simple for a student project):
  • The agent opens a TCP connection, sends one JSON payload, then closes.
  • The server reads until EOF (recv returns b""), then parses the JSON.
  • One-shot connections keep the implementation stateless and easy to reason about.

Threading model:
  • One permanent "acceptor" thread runs self._listen() in the background.
  • For each connecting agent a short-lived "handler" thread is spawned to
    read the payload. It exits when the connection closes.
  • Both are daemon threads so Python exits cleanly when the main process stops.

Academic note (OS / Networks):
  socket.SO_REUSEADDR  — tells the kernel to allow rebinding the port immediately
                          after a restart, even if old TIME_WAIT connections exist.
  socket.SOCK_STREAM   — specifies TCP (reliable, ordered, connection-oriented).
  listen(backlog=50)   — the kernel queues up to 50 incomplete connections while
                          the accept loop is busy.

TODO (Phase 2):
  • Switch to a newline-delimited persistent-connection protocol so agents do not
    pay TCP handshake cost every 10 seconds.
  • Replace thread-per-connection with a thread pool (concurrent.futures) to cap
    resource usage under load.
"""

import json
import logging
import socket
import threading
from typing import Callable

from config.settings import TCP_HOST, TCP_PORT, TCP_BUFFER_SIZE

logger = logging.getLogger(__name__)


class TCPListener:
    """
    Accepts TCP connections from agents and dispatches payload dicts to a callback.

    Parameters
    ----------
    on_data_received : Callable[[dict, str], None]
        Called with (parsed_payload, client_ip) for every valid JSON message.
        This callback runs inside a handler thread — it must be thread-safe.
    """

    def __init__(self, on_data_received: Callable[[dict, str], None]) -> None:
        self.host              = TCP_HOST
        self.port              = TCP_PORT
        self.on_data_received  = on_data_received
        self._server_socket:   socket.socket | None = None
        self._running:         bool = False

    # ── Public interface ──────────────────────────────────────────────────────

    def start(self) -> None:
        """Launch the acceptor thread. Returns immediately (non-blocking)."""
        thread = threading.Thread(
            target=self._listen,
            name="TCPListener-Acceptor",
            daemon=True,
        )
        thread.start()
        logger.info(f"TCP Listener starting on {self.host}:{self.port}")

    def stop(self) -> None:
        """Signal the acceptor loop to exit and close the server socket."""
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except OSError:
                pass
        logger.info("TCP Listener stopped.")

    # ── Acceptor thread ───────────────────────────────────────────────────────

    def _listen(self) -> None:
        """
        Bind, listen, and loop forever accepting client connections.
        Each accepted connection is handed off to a new handler thread.
        """
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self._server_socket.bind((self.host, self.port))
        except OSError as exc:
            logger.critical(f"Cannot bind TCP socket on port {self.port}: {exc}")
            return

        self._server_socket.listen(50)
        self._running = True
        logger.info(f"TCP server accepting connections on {self.host}:{self.port}")

        while self._running:
            try:
                client_sock, addr = self._server_socket.accept()
                client_ip = addr[0]
                logger.debug(f"Connection from {client_ip}:{addr[1]}")

                handler = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_ip),
                    name=f"TCPHandler-{client_ip}",
                    daemon=True,
                )
                handler.start()

            except OSError:
                # Raised when self._server_socket.close() is called during stop()
                break
            except Exception as exc:
                logger.error(f"Accept loop error: {exc}")

    # ── Handler thread ────────────────────────────────────────────────────────

    def _handle_client(self, client_sock: socket.socket, client_ip: str) -> None:
        """
        Read the entire payload sent by one agent, parse JSON, fire callback.

        The loop accumulates chunks until recv() returns b"" (EOF — the agent
        has closed the connection). This handles the case where the OS splits
        a large payload across multiple TCP segments.
        """
        raw = b""
        try:
            while True:
                chunk = client_sock.recv(TCP_BUFFER_SIZE)
                if not chunk:
                    break
                raw += chunk

            if not raw:
                logger.warning(f"Empty payload from {client_ip}; ignoring.")
                return

            payload: dict = json.loads(raw.decode("utf-8"))
            logger.debug(f"Received payload from {client_ip}: {payload}")

            # Hand off to the processing callback (runs in this handler thread)
            self.on_data_received(payload, client_ip)

        except json.JSONDecodeError as exc:
            logger.error(f"Bad JSON from {client_ip}: {exc} | raw={raw[:200]}")
        except Exception as exc:
            logger.error(f"Handler error for {client_ip}: {exc}")
        finally:
            client_sock.close()

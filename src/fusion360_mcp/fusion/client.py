"""TCP bridge to the Fusion 360 add-in.

Blocking I/O runs in asyncio executor so the MCP event loop stays free.
Inject a mock in tests — don't call this class directly from tool handlers.
"""

import asyncio
import logging
import socket

from .errors import FusionConnectionError, FusionOperationError, FusionTimeoutError
from .protocol import FusionRequest, FusionResponse

logger = logging.getLogger(__name__)


class FusionClient:
    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self._send_lock = asyncio.Lock()

    def _send_sync(self, request: FusionRequest) -> FusionResponse:
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                payload = request.model_dump_json().encode() + b"\n"
                sock.sendall(payload)

                chunks: list[bytes] = []
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if chunks[-1].endswith(b"\n"):
                        break

            raw = b"".join(chunks).strip()
            response = FusionResponse.model_validate_json(raw)

            if not response.success:
                raise FusionOperationError(response.error or "Unknown Fusion error")

            return response

        except ConnectionRefusedError as exc:
            raise FusionConnectionError(
                f"Fusion 360 add-in is not running on {self.host}:{self.port}. "
                "Start Fusion 360 and enable the MCP bridge add-in."
            ) from exc
        except TimeoutError as exc:
            raise FusionTimeoutError(
                f"Operation timed out after {self.timeout}s"
            ) from exc

    async def send(self, request: FusionRequest) -> FusionResponse:
        loop = asyncio.get_running_loop()
        if request.timeout is None:
            request.timeout = self.timeout
        async with self._send_lock:
            return await loop.run_in_executor(None, self._send_sync, request)

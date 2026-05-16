#!/usr/bin/env python3

"""Smoke-test the BrainGenix-ERS management API sandbox server."""

from __future__ import annotations

import json
import socket
import subprocess  # nosec B404
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "management_api_server.py"


def _free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    _, port = sock.getsockname()
    sock.close()
    return int(port)


def _request(url: str, method: str = "GET", body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(url, data=data, method=method, headers=headers)
    with urlopen(req, timeout=5) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    port = _free_port()
    process = subprocess.Popen(  # nosec B603
        [sys.executable, str(SERVER), "--host", "127.0.0.1", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    base = f"http://127.0.0.1:{port}"

    try:
        deadline = time.time() + 10
        while True:
            try:
                health = _request(f"{base}/healthz")
                if health["status"] == "ok":
                    break
            except URLError:
                if time.time() >= deadline:
                    raise
                time.sleep(0.2)

        runtime = _request(f"{base}/v1/runtime")
        project = _request(f"{base}/v1/projects/current")
        scene = _request(f"{base}/v1/scenes/current/summary")
        logs = _request(f"{base}/v1/logs/opengl")
        refresh = _request(
            f"{base}/v1/rendering/shadow-maps/refresh",
            method="POST",
            body={"reason": "smoke-test"},
        )
        server_render_start = _request(
            f"{base}/v1/rendering/server/start",
            method="POST",
            body={"contextAPI": "EGL", "frameTransport": "sandbox", "width": 640, "height": 360},
        )
        server_render_status = _request(f"{base}/v1/rendering/server/status")
        server_render_stop = _request(
            f"{base}/v1/rendering/server/stop",
            method="POST",
            body={"reason": "smoke-test"},
        )
        datacenter_load_start = _request(
            f"{base}/v1/datacenter-loading/start",
            method="POST",
            body={"source": "cassandra", "dataset": "sandbox-scene"},
        )
        datacenter_load_status = _request(f"{base}/v1/datacenter-loading/status")
        datacenter_load_cancel = _request(
            f"{base}/v1/datacenter-loading/cancel",
            method="POST",
            body={"reason": "smoke-test"},
        )
        export = _request(
            f"{base}/v1/projects/export",
            method="POST",
            body={"includeBinary": True, "includeConfig": True},
        )

        assert runtime["application"] == "BrainGenix-ERS"
        assert "runtime-summary" in runtime["features"]
        assert "server-rendering-jobs" in runtime["features"]
        assert "datacenter-loading-jobs" in runtime["features"]
        assert project["name"] == "Example Project"
        assert scene["counts"]["models"] >= 0
        assert len(logs["items"]) >= 1
        assert refresh["status"] == "accepted"
        assert server_render_start["serverRendering"]["status"] == "running"
        assert server_render_status["serverRendering"]["width"] == 640
        assert server_render_stop["serverRendering"]["status"] == "stopped"
        assert datacenter_load_start["datacenterLoading"]["status"] == "running"
        assert datacenter_load_status["datacenterLoading"]["dataset"] == "sandbox-scene"
        assert datacenter_load_cancel["datacenterLoading"]["status"] == "cancelled"
        assert export["status"] == "accepted"
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())

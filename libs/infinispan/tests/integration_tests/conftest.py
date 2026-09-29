"""Shared fixtures for integration tests.

Integration tests run against a fresh Infinispan server that this module
starts and stops via a container runtime (docker or podman). A dedicated
container is used so tests never depend on — or interfere with — any
Infinispan server that may already be running on the host.

The container lifecycle is session-scoped: one server is started for the
whole test session and torn down at the end. Each test uses its own uniquely
named cache for isolation.

Environment overrides (all optional):
  - INFINISPAN_IMAGE            container image (default: infinispan/server:15.2)
  - INFINISPAN_CONTAINER_RUNTIME  "docker" or "podman" (default: auto-detect)
  - INFINISPAN_USER             server user (default: admin)
  - INFINISPAN_PASSWORD         server password (default: password)
  - INFINISPAN_EXTERNAL_URL     if set, skip container management and use this
                                already-running server instead (e.g. a CI
                                service container)
"""

import os
import shutil
import socket
import subprocess
import time
import uuid
from typing import Generator, Tuple

import pytest
import requests
from requests.auth import HTTPDigestAuth

IMAGE = os.getenv("INFINISPAN_IMAGE", "infinispan/server:15.2")
USER = os.getenv("INFINISPAN_USER", "admin")
PASSWORD = os.getenv("INFINISPAN_PASSWORD", "password")
EXTERNAL_URL = os.getenv("INFINISPAN_EXTERNAL_URL")

# (url, user, password)
ServerInfo = Tuple[str, str, str]


def _detect_runtime() -> str:
    """Return the container runtime to use, preferring docker."""
    override = os.getenv("INFINISPAN_CONTAINER_RUNTIME")
    if override:
        if not shutil.which(override):
            raise RuntimeError(
                f"INFINISPAN_CONTAINER_RUNTIME={override!r} not found on PATH"
            )
        return override
    for runtime in ("docker", "podman"):
        if shutil.which(runtime):
            return runtime
    raise RuntimeError(
        "Neither 'docker' nor 'podman' found on PATH; a container runtime is "
        "required to start the Infinispan server for integration tests. Set "
        "INFINISPAN_EXTERNAL_URL to use an already-running server instead."
    )


def _free_port() -> int:
    """Find a free TCP port on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


def _wait_healthy(url: str, timeout: float = 90.0) -> None:
    """Poll the REST API until the server answers, or raise on timeout."""
    auth = HTTPDigestAuth(USER, PASSWORD)
    deadline = time.monotonic() + timeout
    last_err: Exception | str = "no attempt made"
    while time.monotonic() < deadline:
        try:
            resp = requests.get(
                f"{url}/rest/v2/caches", auth=auth, timeout=5
            )
            if resp.status_code == 200:
                return
            last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
        except requests.RequestException as exc:
            last_err = exc
        time.sleep(1.0)
    raise RuntimeError(
        f"Infinispan server at {url} did not become healthy within "
        f"{timeout:.0f}s (last error: {last_err})"
    )


@pytest.fixture(scope="session")
def infinispan_server() -> Generator[ServerInfo, None, None]:
    """Start an Infinispan container for the session and yield its coordinates.

    If INFINISPAN_EXTERNAL_URL is set, no container is managed and that server
    is used instead.
    """
    if EXTERNAL_URL:
        _wait_healthy(EXTERNAL_URL)
        yield EXTERNAL_URL, USER, PASSWORD
        return

    runtime = _detect_runtime()
    port = _free_port()
    name = f"langchain-infinispan-test-{uuid.uuid4().hex[:8]}"
    url = f"http://localhost:{port}"

    subprocess.run(
        [
            runtime,
            "run",
            "-d",
            "--rm",
            "--name",
            name,
            "-p",
            f"{port}:11222",
            "-e",
            f"USER={USER}",
            "-e",
            f"PASS={PASSWORD}",
            IMAGE,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    try:
        _wait_healthy(url)
        yield url, USER, PASSWORD
    finally:
        # `--rm` removes the container once it stops.
        subprocess.run(
            [runtime, "stop", name],
            check=False,
            capture_output=True,
            text=True,
        )

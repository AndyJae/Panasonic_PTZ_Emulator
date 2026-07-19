"""HTTP-Integrationstests -- End-to-End ueber FastAPI TestClient bzw. echten
HTTP/TCP-Verbindungen fuer den tatsaechlich per uvicorn gestarteten
CGI-Server (Start/Stop/Notification-Push)."""

from __future__ import annotations

import socket
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from emulator import server
from emulator.notify import parse_notification_frame

cgi_client = TestClient(server.cgi_app)
control_client = TestClient(server.control_app)


@pytest.fixture(autouse=True)
def _stop_manager_after_test():
    yield
    server.manager.stop()


def test_cgi_qid_via_http():
    server.state.reset("AW-UE160")
    resp = cgi_client.get("/cgi-bin/aw_cam", params={"cmd": "QID", "res": 1})
    assert resp.status_code == 200
    assert resp.text == "OID:AW-UE160"


def test_cgi_ptz_iris_via_http():
    server.state.reset("AW-UE160")
    resp = cgi_client.get("/cgi-bin/aw_ptz", params={"cmd": "#AXI555"})
    assert resp.text == "axi555"


def test_control_ui_index_when_stopped():
    resp = control_client.get("/")
    assert resp.status_code == 200
    assert "Server starten" in resp.text


def test_start_stop_lifecycle_binds_real_port():
    port = 18081
    resp = control_client.post("/start", data={"model_id": "AW-UE160", "port": port}, follow_redirects=False)
    assert resp.status_code == 303
    assert server.manager.running

    live = httpx.get(f"http://127.0.0.1:{port}/cgi-bin/aw_cam", params={"cmd": "QID", "res": 1})
    assert live.text == "OID:AW-UE160"

    control_client.post("/stop", follow_redirects=False)
    assert not server.manager.running

    # Windows braucht nach dem Stop teils einen Moment, bis der Port wirklich
    # freigegeben ist (TIME_WAIT) -- ConnectError (sofortige Ablehnung) und
    # ConnectTimeout (Verbindungsversuch verhungert) sind beides gueltige
    # Symptome eines nicht mehr erreichbaren Servers, siehe httpx.TransportError.
    with pytest.raises(httpx.TransportError):
        httpx.get(f"http://127.0.0.1:{port}/cgi-bin/aw_cam", params={"cmd": "QID"}, timeout=2.0)


def test_simulate_change_via_control_ui_pushes_notification():
    cam_port = 18082
    control_client.post("/start", data={"model_id": "AW-UE160", "port": cam_port}, follow_redirects=False)

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    listener_port = listener.getsockname()[1]

    live = httpx.get(
        f"http://127.0.0.1:{cam_port}/cgi-bin/event",
        params={"connect": "start", "my_port": listener_port},
    )
    assert live.status_code == 204

    control_client.post("/simulate-change", data={"command": "OAF:1"}, follow_redirects=False)

    listener.settimeout(3.0)
    conn, _addr = listener.accept()
    data = conn.recv(4096)
    conn.close()
    listener.close()

    assert parse_notification_frame(data) == "OAF:1"


def test_force_er2_lever_via_control_ui():
    cam_port = 18083
    control_client.post("/start", data={"model_id": "AW-UE160", "port": cam_port}, follow_redirects=False)
    control_client.post("/force-er2", follow_redirects=False)

    live = httpx.get(f"http://127.0.0.1:{cam_port}/cgi-bin/aw_cam", params={"cmd": "QID"})
    assert live.text == "ER2:QID"

    live_again = httpx.get(f"http://127.0.0.1:{cam_port}/cgi-bin/aw_cam", params={"cmd": "QID"})
    assert live_again.text == "OID:AW-UE160"

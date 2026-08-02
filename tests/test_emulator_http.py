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


def _real_discovery_request(source_mac: bytes, source_ip: bytes) -> bytes:
    """Bytegleicher Nachbau eines echten Discovery-Requests (siehe
    smart_reset_work/smart_reset/discovery.py::_build_discovery_request) --
    fuer diesen Test bewusst hier dupliziert statt cross-repo importiert
    (CLAUDE.md Regel 4: keine Laufzeitabhaengigkeit auf eine der beiden
    Apps; hier nur ein Test-Fixture, kein Emulator-Code)."""
    return bytes([
        0x00, 0x01, 0x00, 0x2A, 0x00, 0x0D, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        *source_mac, *source_ip,
        0x00, 0x00, 0x20, 0x11, 0x1E, 0x11, 0x23, 0x1F, 0x1E, 0x19, 0x13,
        0x00, 0x00, 0x00, 0x01,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xF0,
        0x00, 0x26, 0x00, 0x20, 0x00, 0x21, 0x00, 0x22, 0x00, 0x23, 0x00, 0x25, 0x00, 0x28,
        0x00, 0x40, 0x00, 0x41, 0x00, 0x42, 0x00, 0x44, 0x00, 0xA5, 0x00, 0xA6, 0x00, 0xA7,
        0x00, 0xA8, 0x00, 0xAD, 0x00, 0xB3, 0x00, 0xB4, 0x00, 0xB7, 0x00, 0xB8,
        0xFF, 0xFF, 0x12, 0x21,
    ])


def test_udp_discovery_responds_to_real_request_and_stops_with_server():
    cam_port = 18084
    control_client.post("/start", data={"model_id": "AW-UE100", "port": cam_port}, follow_redirects=False)

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_sock.settimeout(2.0)
    request = _real_discovery_request(bytes([0x02, 0, 0, 0, 0, 1]), bytes([127, 0, 0, 1]))
    client_sock.sendto(request, ("127.0.0.1", 10670))
    data, _addr = client_sock.recvfrom(4096)
    client_sock.close()

    assert data[:4] == b"\x00\x01\x01\x75"
    assert b"AW-UE100" in data

    control_client.post("/stop", follow_redirects=False)

    # Nach dem Stop antwortet auf Port 10670 niemand mehr. Windows liefert
    # dafuer nicht immer einen sauberen Timeout, sondern surfacet die vom
    # Kernel empfangene ICMP-Port-Unreachable-Rueckmeldung als
    # ConnectionResetError (WinError 10054) auf dem naechsten recvfrom() --
    # beides ist gueltige Evidenz fuer "niemand hoert mehr zu", analog zu
    # ConnectError/ConnectTimeout in test_start_stop_lifecycle_binds_real_port.
    no_reply_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    no_reply_sock.settimeout(1.0)
    no_reply_sock.sendto(request, ("127.0.0.1", 10670))
    try:
        no_reply_sock.recvfrom(4096)
        assert False, "expected no reply after stop"
    except (socket.timeout, ConnectionResetError, OSError):
        pass
    finally:
        no_reply_sock.close()

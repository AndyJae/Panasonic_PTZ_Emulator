"""Unit-Tests fuer emulator/discovery.py::build_discovery_response()."""

from __future__ import annotations

from emulator.discovery import build_discovery_response


def _tlv_index(data: bytes) -> dict[int, bytes]:
    """Minimaler, eigenstaendiger TLV-Parser fuer die Tests -- absichtlich
    keine Wiederverwendung von smart_reset_work-Code (siehe CLAUDE.md,
    Regel 4: kein Laufzeit-Import einer der beiden Apps)."""
    index: dict[int, bytes] = {}
    cursor = 58
    while cursor < len(data) - 4:
        field_id = (data[cursor] << 8) | data[cursor + 1]
        length = (data[cursor + 2] << 8) | data[cursor + 3]
        start = cursor + 4
        end = start + length
        if end > len(data):
            break
        index[field_id] = data[start:end]
        cursor = end
    return index


def test_header_matches_reader_contract():
    resp = build_discovery_response("AW-UE160", "127.0.0.1", 8081)
    assert resp[:4] == b"\x00\x01\x01\x75"
    assert len(resp) > 58


def test_mac_embedded_at_bytes_6_to_12():
    resp = build_discovery_response("AW-UE160", "127.0.0.1", 8081)
    mac = resp[6:12]
    assert mac[0] == 0x02  # lokal verwaltete Platzhalter-MAC
    assert mac[4:6] == bytes([(8081 >> 8) & 0xFF, 8081 & 0xFF])


def test_all_mandatory_fields_present_and_doubled():
    resp = build_discovery_response("AW-UE160", "192.168.1.50", 8081)
    fields = _tlv_index(resp)

    for primary, alternate in [(0x20, 0xA0), (0x21, 0xA1), (0x22, 0xA2)]:
        assert primary in fields and alternate in fields
        assert fields[primary] == fields[alternate]

    assert fields[0x20] == bytes([192, 168, 1, 50])
    assert len(fields[0x23]) == 8  # DNS primaer+sekundaer
    assert fields[0x25] == fields[0x44] == bytes([0x1F, 0x91])  # Port 8081


def test_model_and_name_fields_null_terminated_ascii():
    resp = build_discovery_response("AW-UE100", "127.0.0.1", 8081)
    fields = _tlv_index(resp)
    assert fields[0xA8].rstrip(b"\x00").decode("ascii") == "AW-UE100"
    assert fields[0xA7].rstrip(b"\x00").decode("ascii") == "AW-UE100 (emulator)"


def test_invalid_ip_falls_back_to_loopback():
    resp = build_discovery_response("AW-UE160", "not-an-ip", 8081)
    fields = _tlv_index(resp)
    assert fields[0x20] == bytes([127, 0, 0, 1])

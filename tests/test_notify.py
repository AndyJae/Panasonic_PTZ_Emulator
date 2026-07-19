"""Tests fuer emulator/notify.py -- Frame-Encode/Decode-Rundlauf."""

from emulator.notify import encode_notification_frame, parse_notification_frame


def test_encode_decode_roundtrip():
    frame = encode_notification_frame("OSA:0D:1")
    assert parse_notification_frame(frame) == "OSA:0D:1"


def test_frame_has_fixed_header_and_trailer_length():
    frame = encode_notification_frame("DCB:1")
    info = b"\r\nDCB:1\r\n"
    assert len(frame) == 22 + 2 + 4 + len(info) + 24


def test_parse_returns_none_for_too_short_frame():
    assert parse_notification_frame(b"\x00" * 10) is None


def test_parse_returns_none_without_crlf_delimited_command():
    header = b"\x00" * 28
    assert parse_notification_frame(header + b"no-crlf-here") is None


def test_encode_decode_roundtrip_for_trigger_command_without_value():
    frame = encode_notification_frame("OAS")
    assert parse_notification_frame(frame) == "OAS"

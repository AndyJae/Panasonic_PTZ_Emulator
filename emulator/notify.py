"""emulator/notify.py -- Update-Notification-Frame-Encoding/-Decoding.

Reine Funktionen, keine Socket-/FastAPI-Kopplung (Push passiert in state.py/
server.py). Frame-Format aus docs/specs/AW-UE160_InterfaceSpecification_E.pdf
§5-2 und docs/specs/HDIntegratedCamera_InterfaceSpecifications-E.pdf §4.2:

    Reserve(22B) Size(2B) Reserve(4B) info(<=504B) Reserve(24B)
    info = "\\r\\n" + <command-response-string> + "\\r\\n"   (z. B. "\\r\\nDCB:1\\r\\n")

Das Size-Feld ist in keiner lokalen PDF hinsichtlich Byte-Order dokumentiert
(siehe reference/smart_reset_work_camera_plugins/notify.py) -- big-endian
wird hier als willkuerliche, aber konsistente Wahl uebernommen (1:1 Port,
keine inhaltliche Aenderung); das Decoding verlaesst sich nicht auf dieses
Feld, sondern lokalisiert den CRLF-getrennten Befehl per Inhalt.
"""

from __future__ import annotations

import struct

_RESERVE_HEAD = 22
_SIZE_FIELD = 2
_RESERVE_MID = 4
_RESERVE_TAIL = 24
_HEADER_LEN = _RESERVE_HEAD + _SIZE_FIELD + _RESERVE_MID


def encode_notification_frame(command: str) -> bytes:
    """Baut einen Update-Notification-Frame fuer `command` (z. B. "OSA:0D:1")."""
    info = b"\r\n" + command.encode("ascii", errors="replace") + b"\r\n"
    return (
        b"\x00" * _RESERVE_HEAD
        + struct.pack(">H", len(info) + 8)
        + b"\x00" * _RESERVE_MID
        + info
        + b"\x00" * _RESERVE_TAIL
    )


def parse_notification_frame(data: bytes) -> str | None:
    """Extrahiert den gepushten Kommando-String aus einem rohen Frame.

    Gibt None zurueck, wenn der Frame zu kurz ist oder keinen CRLF-
    getrennten Befehl nach dem festen 28-Byte-Header enthaelt.
    """
    if len(data) <= _HEADER_LEN:
        return None
    parts = data[_HEADER_LEN:].split(b"\r\n", 2)
    if len(parts) < 2:
        return None
    cmd = parts[1].decode("ascii", errors="replace").strip()
    return cmd or None

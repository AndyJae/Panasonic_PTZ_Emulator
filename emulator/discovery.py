"""emulator/discovery.py -- UDP-Discovery-Antwort (Panasonic "Easy IP Setup").

Reine Funktionen (`build_discovery_response`) plus ein Socket-Loop
(`discovery_responder_loop`), analog zur Trennung in notify.py.

Deckt nur die *Lese*-Seite des Protokolls ab: eine Kamera antwortet auf
einen UDP-Broadcast-Discovery-Request mit ihrer aktuellen Netzwerk-
konfiguration (IP/Netmask/Gateway/DNS/Port/Modell/Name). Die *Schreib*-Seite
(IP setzen/DHCP-Reset ueber einen JSON+TLV-Handshake auf den Ports
10671/10672 + 10669/10670) ist bewusst nicht Teil dieses Moduls -- siehe
CLAUDE.md.

**Herkunft/Verifikation:** 1:1-Port aus `smart_reset_work/smart_reset/
discovery.py` (dort in einer separaten Chat-Session gegen die offiziellen
Panasonic-Interface-Spec-PDFs sowie unabhaengig gegen eine oeffentliche
Referenzimplementierung des Wire-Formats geprueft -- siehe dortige
CLAUDE.md, Abschnitt "Panasonic network configuration"). `docs/specs/`
existiert in diesem Repo nicht (siehe CLAUDE.md, "Referenzmaterial ...
entfernt"), daher hier keine erneute PDF-Verifikation moeglich oder
beansprucht -- nur der bereits verifizierte Byte-Level-Vertrag wird
uebernommen, keine neuen Annahmen. Live gegenverifiziert in dieser Session
per echtem UDP-Roundtrip gegen `smart_reset_work`s eigenen Discovery-Client
(siehe tests/test_discovery.py und tests/test_emulator_http.py).
"""

from __future__ import annotations

import socket
import threading

DISCOVERY_REQUEST_PORT = 10670

# Primaer-/Alternate-TLV-Feld-ID-Paare, wie vom lesenden Client (siehe
# smart_reset_work/smart_reset/discovery.py::_parse_camera_configuration)
# gefordert -- jedes Feld muss doppelt vorkommen, sonst wird die Antwort
# verworfen.
_FIELD_IP, _FIELD_ALT_IP = 0x0020, 0x00A0
_FIELD_NETMASK, _FIELD_ALT_NETMASK = 0x0021, 0x00A1
_FIELD_GATEWAY, _FIELD_ALT_GATEWAY = 0x0022, 0x00A2
_FIELD_DNS = 0x0023
_FIELD_PORT, _FIELD_ALT_PORT = 0x0025, 0x0044
_FIELD_MODEL = 0x00A8
_FIELD_NAME = 0x00A7


def _tlv(field_id: int, value: bytes) -> bytes:
    return bytes([
        (field_id >> 8) & 0xFF, field_id & 0xFF,
        (len(value) >> 8) & 0xFF, len(value) & 0xFF,
    ]) + value


def _placeholder_mac(port: int) -> bytes:
    """Lokal verwaltete Platzhalter-MAC; die letzten beiden Bytes kommen vom
    CGI-Port, damit mehrere gleichzeitig laufende Emulator-Instanzen beim
    MAC-basierten Dedup des lesenden Clients nicht kollidieren."""
    return bytes([0x02, 0x00, 0x00, 0x00, (port >> 8) & 0xFF, port & 0xFF])


def build_discovery_response(model_id: str, ip: str, port: int) -> bytes:
    """
    Baut ein UDP-Discovery-Antwort-Datagramm, das smart_reset_work's
    `_parse_camera_configuration()` akzeptiert: hartkodierter Header
    `b"\\x00\\x01\\x01\\x75"`, danach TLV-Felder ab Byte 58 -- IP/Netmask/
    Gateway doppelt (Primaer+Alternate-Feld-ID), DNS, Port doppelt, Modell,
    Kameraname. Alle dort als Pflichtfelder behandelt; eine Antwort ohne
    eines davon wird beim Empfaenger stillschweigend verworfen.
    """
    mac = _placeholder_mac(port)
    try:
        ip_bytes = bytes(int(octet) for octet in ip.split("."))
        if len(ip_bytes) != 4:
            raise ValueError
    except ValueError:
        ip_bytes = bytes([127, 0, 0, 1])
    netmask_bytes = bytes([255, 255, 255, 0])
    gateway_bytes = bytes([ip_bytes[0], ip_bytes[1], ip_bytes[2], 1])
    dns_bytes = bytes(8)  # 0.0.0.0 primaer + sekundaer
    port_bytes = bytes([(port >> 8) & 0xFF, port & 0xFF])
    model_bytes = model_id.encode("ascii", errors="ignore") + b"\x00"
    name_bytes = f"{model_id} (emulator)".encode("ascii", errors="ignore") + b"\x00"

    header = (bytes([0x00, 0x01, 0x01, 0x75, 0x00, 0x00]) + mac + ip_bytes).ljust(58, b"\x00")

    tlv = b"".join([
        _tlv(_FIELD_IP, ip_bytes), _tlv(_FIELD_ALT_IP, ip_bytes),
        _tlv(_FIELD_NETMASK, netmask_bytes), _tlv(_FIELD_ALT_NETMASK, netmask_bytes),
        _tlv(_FIELD_GATEWAY, gateway_bytes), _tlv(_FIELD_ALT_GATEWAY, gateway_bytes),
        _tlv(_FIELD_DNS, dns_bytes),
        _tlv(_FIELD_PORT, port_bytes), _tlv(_FIELD_ALT_PORT, port_bytes),
        _tlv(_FIELD_MODEL, model_bytes),
        _tlv(_FIELD_NAME, name_bytes),
    ])
    return header + tlv


def create_discovery_socket() -> socket.socket | None:
    """Bindet 0.0.0.0:10670 fuer den Discovery-Responder. Gibt None zurueck,
    wenn der Port nicht gebunden werden kann (z. B. durch einen anderen,
    noch laufenden Prozess belegt) -- der Aufrufer entscheidet, wie er
    diesen Fehlschlag meldet (siehe `ServerManager.discovery_error` in
    server.py; anders als ein fehlgeschlagener CGI-Bind ist das kein
    fataler Fehler, nur "per Scan Network nicht auffindbar")."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", DISCOVERY_REQUEST_PORT))
        sock.settimeout(0.5)
    except OSError:
        sock.close()
        return None
    return sock


def discovery_responder_loop(
    sock: socket.socket, stop_event: threading.Event, host: str, cgi_port: int, model_id: str
) -> None:
    """Nutzt einen bereits gebundenen Socket (siehe `create_discovery_socket()`)
    und antwortet auf jeden eingehenden Discovery-Request per
    `build_discovery_response()` direkt an die Absenderadresse. Laeuft, bis
    `stop_event` gesetzt wird (Poll-Intervall 0.5s); schliesst den Socket
    beim Beenden."""
    try:
        while not stop_event.is_set():
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            if len(data) < 2 or data[:2] != b"\x00\x01":
                continue
            response = build_discovery_response(model_id, host, cgi_port)
            try:
                sock.sendto(response, addr)
            except OSError:
                pass
    finally:
        sock.close()

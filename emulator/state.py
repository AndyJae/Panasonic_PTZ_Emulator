"""emulator/state.py -- simulierter Kamerazustand pro laufender Emulator-
Instanz (ein CameraState pro gestartetem CGI-Server, siehe server.py).
"""

from __future__ import annotations

import socket
from types import ModuleType

from emulator.models import resolve_model
from emulator.notify import encode_notification_frame

_GAIN_ZERO_DB_DATA = 0x08


class CameraState:
    def __init__(self, model_id: str) -> None:
        self.model_id: str = model_id
        self.module: ModuleType | None = None

        # Generischer Doppelpunkt-Store (smart_reset_work-Vorbild, siehe
        # dispatch.py::_dispatch_generic) -- Key ohne fuehrenden
        # Prefix-Buchstaben, z. B. "SA:0D" fuer "OSA:0D:1".
        self.generic_values: dict[str, str] = {}
        self.generic_prefixes: dict[str, str] = {}

        # FEATURES-Query-Werte: query-Kommando (z. B. "QSE:33") -> zuletzt
        # gesetzter Rohwert (z. B. "1").
        self.feature_values: dict[str, str] = {}

        # Gain/Pedestal-Rohdaten (Encoding/Range-Check siehe dispatch.py).
        self.gain_data: int = _GAIN_ZERO_DB_DATA
        self.pedestal_data: int = 0

        # Iris/ND/Bars -- modellunabhaengig (siehe dispatch.py-Docstring).
        self.iris_data: int = 0xAAA
        self.auto_iris: bool = False
        self.nd_index: int = 0
        self.bars_on: bool = False

        # ER2-Einmal-Schalter (manueller Test-Hebel, Nutzerentscheid -- kein
        # PDF-Beleg fuer eine automatische busy-Ausloesebedingung).
        self.force_er2_once: bool = False

        # Update-Notification-Listener: my_port -> Client-Host (registriert
        # ueber GET /cgi-bin/event?connect=start).
        self.listeners: dict[int, str] = {}

        self.log: list[str] = []

        self.reset(model_id)

    def reset(self, model_id: str) -> None:
        self.model_id = model_id
        self.module = resolve_model(model_id)
        self.generic_values.clear()
        self.generic_prefixes.clear()
        self.feature_values.clear()
        self.gain_data = _GAIN_ZERO_DB_DATA
        self.pedestal_data = getattr(self.module, "PEDESTAL_CENTER_DATA", 0) if self.module else 0
        self.iris_data = 0xAAA
        self.auto_iris = False
        self.nd_index = 0
        self.bars_on = False
        self.force_er2_once = False
        self.listeners.clear()
        self.log.clear()

    def record(self, command: str, response: str) -> None:
        self.log.append(f"{command} -> {response}")
        self.log = self.log[-50:]

    def push_notification(self, command: str) -> None:
        """Oeffnet fuer jeden registrierten Listener eine kurzlebige
        TCP-Verbindung und pusht einen Update-Notification-Frame (siehe
        notify.py). Verbindungsfehler werden verworfen -- ein Listener, der
        nicht mehr erreichbar ist, blockiert die anderen nicht."""
        frame = encode_notification_frame(command)
        for my_port, host in list(self.listeners.items()):
            try:
                with socket.create_connection((host, my_port), timeout=2.0) as sock:
                    sock.sendall(frame)
            except OSError:
                pass

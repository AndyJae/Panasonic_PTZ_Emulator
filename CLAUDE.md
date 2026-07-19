# CLAUDE.md — Panasonic_PTZ_Emulator

## Vorhaben

Ein eigenständiges Panasonic-PTZ-Kamera-Emulator-Tool, das von zwei
unabhängigen Apps als externer Test-Prozess genutzt werden kann, ohne dass
eine der beiden Apps zur Laufzeit von diesem Repo (oder umgekehrt) abhängt:

- **`C:\smart_reset_work`** (veröffentlicht als `smart-reset-browser`) —
  Browser-basiertes Reset-/Steuerungs-/NDI-Tool.
- **`C:\PTZ_Control`** — MIDI-Shading-Controller (Behringer X-Touch
  Extender) für PTZ-Kameras.

Beide Apps sprechen dasselbe Panasonic-CGI-Protokoll gegen echte Kameras
und pflegen bisher **je eine eigene, unabhängige Emulator-Implementierung**
(`tools/panasonic_emulator.py` in beiden Repos), die jeweils eng an das
interne Kamera-Katalog-Format der eigenen App gekoppelt ist. Das führt zu
doppelter Pflege und tatsächlich schon aufgetretenem Format-Drift (siehe
`TODO.md`, Abschnitt 0, für konkrete bereits gefundene Abweichungen
zwischen den beiden Katalogen).

Ziel dieses Repos: **ein** Emulator-Tool, das:
1. keine der beiden Apps importiert oder sonst zur Laufzeit voraussetzt,
2. beide bisher genutzten Protokoll-Dialekte abdeckt (Doppelpunkt-basierte
   `O<sub>:addr:value`/`Q<sub>:addr`-Kommandos UND doppelpunktlose
   `#AXI`/`#GI`/`#R`-Kommandos),
3. das vollständigere Verhalten aus beiden Vorbildern vereint (u. a.
   Update-Notification-Push aus `smart_reset_work`, modellabhängige
   Gain-/Pedestal-Simulation aus `PTZ_Control`),
4. als einzige Quelle der Wahrheit für "was simuliert dieses Tool" dient —
   beide Apps zeigen künftig auf dieses Repo statt auf ihre eigene Kopie.

**Aktueller Stand:** Scaffolding abgeschlossen (Git-Repo, venv,
`requirements.txt`, kopiertes Referenzmaterial unter `reference/` und
`docs/specs/`). Die eigentliche Zusammenführung ist noch nicht begonnen —
siehe [TODO.md](TODO.md) für den geplanten Ablauf. Bis dahin enthält dieses
Repo keinen eigenen Emulator-Code, nur Referenzkopien.

### Referenzmaterial (`reference/`, `docs/specs/`)

Alles unter `reference/` ist eine **Kopie zum Zeitpunkt des Scaffoldings**
(2026-07-19), keine lebende Verbindung zu den Quell-Repos — spätere
Änderungen dort fließen nicht automatisch hierher. Bei Unklarheiten über
den aktuellen Stand der Quell-Repos: dort nachsehen, nicht von dieser Kopie
ausgehen.

| Datei/Ordner | Herkunft | Inhalt |
|---|---|---|
| `reference/smart_reset_work_emulator.py` | `smart_reset_work/tools/panasonic_emulator.py` | Generischer Dispatch, Update-Notification-Push |
| `reference/ptz_control_emulator.py` | `PTZ_Control/tools/panasonic_emulator.py` | Explizite Pro-Befehl-Behandlung, Gain/Pedestal, `#`-Befehle |
| `reference/ptz_control_panasonic_aw_driver.py` | `PTZ_Control/drivers/panasonic_aw.py` | Realer Treiber inkl. Notification-Parsing (`_handle_notification`) — Referenz für Gain-/Pedestal-Decodierung |
| `reference/smart_reset_work_camera_plugins/` | `smart_reset_work/camera_plugins/panasonic/` | `UI_BUTTONS`/`UI_DROPDOWNS`/`RESET_COMMANDS`/`UI_FEATURE_QUERIES` je Modell (19 Dateien inkl. `notify.py`, `transport.py`, `base.py`) |
| `reference/ptz_control_panasonic_models/` | `PTZ_Control/drivers/panasonic_models/` | `BUTTON_FEATURES` + Gain/Pedestal-Konstanten je Modell (eigenständig gegen PDFs verifiziert, teils abweichend von smart_reset_work — siehe TODO.md) |
| `reference/smart_reset_work_CLAUDE.md`, `reference/ptz_control_CLAUDE.md` | jeweiliges Repo | Volltext-Kopie der Quell-Regeln/-Historie, Basis für die Regeln unten |
| `docs/specs/` | beide Repos (identischer Satz) | Offizielle Panasonic-Interface-Spec-PDFs — Quelle der Wahrheit für jeden Kamerabefehl |

---

## Allgemeine Regeln

Zusammengeführt aus den Arbeitsregeln beider Quell-Repos (siehe
`reference/smart_reset_work_CLAUDE.md` und `reference/ptz_control_CLAUDE.md`
für den vollen Wortlaut/Kontext). Wo beide Quellen dieselbe Regel mit
unterschiedlicher Betonung haben, ist hier die strengere Fassung
übernommen.

### 1. Keine Halluzinationen, keine erfundenen Kommandos

- Keine Kamera-Befehle, Wertebereiche oder Antwortformate annehmen, die
  nicht in `docs/specs/` stehen oder in einer der beiden Referenzquellen
  bereits PDF-verifiziert dokumentiert sind.
- Bei Widerspruch zwischen den beiden Referenzquellen: `docs/specs/` direkt
  prüfen, nicht eine der beiden Quellen bevorzugen, nur weil sie zuerst
  gelesen wurde.
- Unklarheiten explizit benennen und nachfragen statt zu raten — gilt auch
  für Architektur-/Scope-Fragen, nicht nur Gerätedetails.

### 2. Nur aus verifizierbaren Quellen arbeiten

- Vor Aussagen wie "funktioniert", "ist korrekt", "entspricht der Kamera"
  immer die Bestätigung durch PDF-Zitat, Test oder tatsächliche Ausführung
  benennen.
- Wenn etwas nicht verifiziert werden kann: sagen "nicht verifiziert" /
  "in der Spezifikation nicht definiert" statt "sollte funktionieren".

### 3. Minimal-invasiv, chirurgisch

- Kleinstmögliche gezielte Änderung statt Umbau.
- Referenzmaterial unter `reference/` nicht "nebenbei" verbessern oder
  umformatieren — es ist eine Momentaufnahme, keine lebende Codebasis.
- Bestehenden Stil im entstehenden Emulator-Code nicht ohne Auftrag ändern.

### 4. Scope strikt einhalten

- Dieses Repo baut ein Emulator-Tool — keine Reset-Sequenz-Logik, keine
  MIDI-Mapping-Logik, keine sonstigen App-spezifischen Features aus einer
  der beiden Quellen übernehmen, nur was zur Protokoll-Simulation gehört.
- Änderungen an `smart_reset_work` oder `PTZ_Control` selbst (z. B. um sie
  auf dieses Tool umzustellen) gehören nicht in dieses Repo, siehe
  `TODO.md` Abschnitt 6.

### 5. Tests zuerst und realitätsnah

- Keine Test-only-Methoden im Emulator-Code.
- Verifikation gegen echtes Verhalten (beide Apps, echte HTTP-Requests),
  nicht nur isolierte Annahmen.

### 6. Abschlussregel

Vor jeder Aussage "fertig"/"gelöst": durch Test, Log oder nachvollziehbare
Datei-/PDF-Evidenz belegen. Sonst: "noch unbestätigt".

---

## Stack (vorläufig, siehe `requirements.txt`)

- Python 3.10+ (venv bereits unter `.venv/` eingerichtet)
- FastAPI + uvicorn (wie beide Vorbilder)
- `python-multipart` (für Form-Handling der Control-UI)

Keine Abhängigkeit auf `requests`, `numpy`, `pydantic`, `mido` o. Ä. aus
einer der beiden Quell-Apps — dieses Tool ist reiner Server, kein Client,
kein MIDI, keine NDI/Bildverarbeitung.

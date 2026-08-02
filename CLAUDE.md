# CLAUDE.md — Panasonic_PTZ_Emulator

## Vorhaben

Ein eigenständiges Panasonic-PTZ-Kamera-Emulator-Tool, das von zwei
unabhängigen Apps als externer Test-Prozess genutzt werden kann, ohne dass
eine der beiden Apps zur Laufzeit von diesem Repo (oder umgekehrt) abhängt:

- **`C:\GitHub\smart_reset_work`** (veröffentlicht als `smart-reset-browser`) —
  Browser-basiertes Reset-/Steuerungs-/NDI-Tool.
- **`C:\GitHub\X-Touch_PTZ_Control_Work`** (veröffentlicht als
  `X-Touch_PTZ_Control`) — MIDI-Shading-Controller (Behringer X-Touch
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

**Aktueller Stand (2026-07-27):** die Zusammenführung ist inzwischen
weitgehend umgesetzt, nicht mehr nur geplant — `emulator/` enthält einen
eigenständigen Dispatch (`dispatch.py`), 17 Modellkataloge
(`emulator/models/*.py`), Zustandsverwaltung (`state.py`),
Update-Notification-Encoding/-Push (`notify.py`) sowie Control-UI + CGI-Server
(`server.py`, Einstiegspunkt `main.py`, Tray-Icon `tray.py`) — TODO.md-Schritte
1–5 und 7 sind laut Commit-Historie (`0a161f9 Implement merged Panasonic PTZ
CGI emulator (TODO.md steps 1-5, 7)`, danach `186a58c`/`9632171` für
Einstiegspunkt/Tray-Icon) bereits erledigt, inklusive der in TODO.md Schritt 4
noch als fehlend geführten ER2/ER3-Simulation und dem automatischen
Notification-Push bei jeder Set-Änderung (nicht nur beim manuellen
"simulate"-Knopf). Eigene Testsuite: 43/43 Tests grün (`pytest`, Stand
2026-07-27). Zusätzlich live gegen den echten `PanasonicAWDriver` aus
`PTZ_Control` verifiziert (echter HTTP-Roundtrip, kein Mock): Iris-Setzen/
-Lesen, Gain inkl. ER3-Wertebereichsfehler und Auto/AGC-Zustand, Pedestal,
Button-Feature-Toggle (`auto_focus`) und Update-Notification-Push kamen
korrekt beim Treiber an.

**UDP-Discovery-Antwort ("Easy IP Setup") ergänzt (2026-08-02):** neues
Modul `emulator/discovery.py` (`build_discovery_response`,
`discovery_responder_loop`) — der Emulator antwortet jetzt auf UDP-
Discovery-Requests (Port 10670 → Antwort direkt an den Absender, keine
feste Response-Portbindung nötig), damit `smart_reset_work`s "Scan
Network" ihn findet. `ServerManager` in `server.py` startet/stoppt den
Responder-Thread zusammen mit dem CGI-Server. **1:1-Port aus
`smart_reset_work/smart_reset/discovery.py`**, wo das Byte-Format in einer
separaten Session gegen die offiziellen Interface-Spec-PDFs sowie
unabhängig gegen eine öffentliche Referenzimplementierung verifiziert
wurde (siehe `discovery.py`'s Docstring hier) — da `docs/specs/` in diesem
Repo entfernt ist (s. o.), wurde hier keine erneute PDF-Prüfung
durchgeführt, nur der bereits verifizierte Vertrag übernommen.

Deckt nur die *Lese*-Seite ab (Discovery). Die *Schreib*-Seite (IP setzen/
DHCP-Reset über den JSON+TLV-Handshake auf Port 10671/10672 + 10669/10670)
ist **nicht** implementiert — ein "Set IP"-Versuch aus `smart_reset_work`
gegen diesen Emulator bleibt unbeantwortet (sauberer Fehler, kein Crash).
Bewusste Scope-Grenze dieser Änderung, keine Lücke.

Getestet: 6 neue Tests (`tests/test_discovery.py` — Paketaufbau isoliert;
`tests/test_emulator_http.py::test_udp_discovery_responds_to_real_request_and_stops_with_server`
— echter UDP-Roundtrip mit einem bytegleichen Nachbau eines realen
Discovery-Requests gegen einen tatsächlich per `ServerManager` gestarteten
Server, plus Verifikation dass nach `/stop` niemand mehr antwortet).
Gesamte Suite: 49/49 grün (`pytest`, Stand 2026-08-02).

**Cross-repo live-verifiziert (2026-08-02):** `smart_reset_work`s eigener,
unveränderter `smart_reset/discovery.py::discover_cameras()`-Client hat
diesen Emulator (über `ServerManager.start()` gestartet) via echtem
UDP-Broadcast gefunden und korrekt geparst — Modell, IP, Port, MAC,
Netmask, Gateway kamen alle richtig an. Kein Mock, zwei echte Prozesse
über echte Sockets (Test lief zwar im selben Python-Prozess, aber mit
echten OS-Sockets, nicht in-memory). Direkt reproduziert, was in
`smart_reset_work`s eigener `CLAUDE.md` als offene Lücke vermerkt war.

**Dabei gefunden und behoben:** ein erster Testlauf schlug fehl, weil ein
Prozess aus einem vorherigen Testlauf Port 10670 noch belegt hielt — der
Discovery-Bind-Fehlschlag blieb dabei komplett unsichtbar (Kamera lief,
`discovery_error` existierte noch nicht, kein Hinweis irgendwo). Deshalb
`create_discovery_socket()`/`discovery_responder_loop()` getrennt (analog
zu `smart_reset_work`s eigenem `create_discovery_socket()`/
`discover_cameras()`-Split) und `ServerManager.discovery_error` ergänzt,
sichtbar als Warnung in der Control-UI, sobald der Bind fehlschlägt —
sonst ein rein stiller Fehlerfall gewesen.

**Weiterhin offen (TODO.md Schritt 6, nicht Teil dieses Repos):** weder
`smart_reset_work` noch `PTZ_Control` sind bisher auf dieses Tool umgestellt
— beide nutzen weiterhin ihre eigene `tools/panasonic_emulator.py`-Kopie.
Kein Live-Test gegen `smart_reset_work` durchgeführt (dessen Consumer-Code
zeigt noch auf keinen externen Emulator). Cross-Modell-Gate (Kommando eines
anderen Modells → `ER1`) nicht separat live verifiziert, nur im Code
vorhanden.

### Referenzmaterial (`reference/`, `docs/specs/`) — entfernt für die Veröffentlichung

**Entfernt (Nutzerauftrag 2026-07-27, Vorbereitung auf ein öffentliches Repo):**
`reference/` und `docs/specs/` enthielten eine echte interne Kamera-IP
(`192.168.0.10`, aus der kopierten `smart_reset_work_CLAUDE.md`) sowie sieben
offizielle, urheberrechtlich geschützte Panasonic/Behringer-Interface-Spec-PDFs
— beides nicht für ein öffentliches Repo geeignet. Da beide Ordner bereits im
allerersten Commit (`Scaffold ...`) enthalten waren, reichte ein einfaches
`git rm` nicht aus (die Dateien wären über die Commit-Historie weiterhin
abrufbar geblieben) — die gesamte Historie wurde per `git filter-repo --path
reference --invert-paths --path docs --invert-paths` neu geschrieben und
force-gepusht, danach `.gitignore` um `reference/`/`docs/` ergänzt. Beide
Ordner existieren weiterhin lokal (nicht Teil des Repos) unter
`C:\GitHub\Panasonic_PTZ_Emulator_reference_backup` für die Weiterarbeit auf
dieser Maschine.

Ursprünglicher Inhalt (jetzt nur noch im lokalen Backup, nicht mehr im Repo):

| Datei/Ordner | Herkunft | Inhalt |
|---|---|---|
| `reference/smart_reset_work_emulator.py` | `smart_reset_work/tools/panasonic_emulator.py` | Generischer Dispatch, Update-Notification-Push |
| `reference/ptz_control_emulator.py` | `PTZ_Control/tools/panasonic_emulator.py` | Explizite Pro-Befehl-Behandlung, Gain/Pedestal, `#`-Befehle |
| `reference/ptz_control_panasonic_aw_driver.py` | `PTZ_Control/drivers/panasonic_aw.py` | Realer Treiber inkl. Notification-Parsing (`_handle_notification`) — Referenz für Gain-/Pedestal-Decodierung |
| `reference/smart_reset_work_camera_plugins/` | `smart_reset_work/camera_plugins/panasonic/` | `UI_BUTTONS`/`UI_DROPDOWNS`/`RESET_COMMANDS`/`UI_FEATURE_QUERIES` je Modell (19 Dateien inkl. `notify.py`, `transport.py`, `base.py`) |
| `reference/ptz_control_panasonic_models/` | `PTZ_Control/drivers/panasonic_models/` | `BUTTON_FEATURES` + Gain/Pedestal-Konstanten je Modell (eigenständig gegen PDFs verifiziert, teils abweichend von smart_reset_work) |
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

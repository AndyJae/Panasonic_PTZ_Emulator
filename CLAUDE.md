# CLAUDE.md — Panasonic_PTZ_Emulator

## Non-negotiable: nie erfinden

Keine Kamera-Befehle, Wertebereiche oder Antwortformate annehmen, die nicht in `docs/specs/`
stehen oder in einer der beiden Referenzquellen bereits PDF-verifiziert dokumentiert sind (siehe
CHANGELOG.md, "Reference material removed" — `docs/specs/`/`reference/` sind nicht mehr Teil
dieses Repos, nur noch lokal unter `C:\GitHub\Panasonic_PTZ_Emulator_reference_backup`). Bei
Widerspruch zwischen den beiden Referenzquellen: die Spec-PDFs direkt prüfen, nicht eine der
beiden Quellen bevorzugen, nur weil sie zuerst gelesen wurde. Unklarheiten explizit benennen und
nachfragen statt zu raten — gilt auch für Architektur-/Scope-Fragen, nicht nur Gerätedetails.

## Vorhaben

Ein eigenständiges Panasonic-PTZ-Kamera-Emulator-Tool, das von zwei unabhängigen Apps als
externer Test-Prozess genutzt werden kann, ohne dass eine der beiden Apps zur Laufzeit von diesem
Repo (oder umgekehrt) abhängt:

- **`C:\GitHub\smart_reset_work`** (veröffentlicht als `smart-reset-browser`) —
  Browser-basiertes Reset-/Steuerungs-/NDI-Tool.
- **`C:\GitHub\X-Touch_PTZ_Control_Work`** (veröffentlicht als
  `X-Touch_PTZ_Control`) — MIDI-Shading-Controller (Behringer X-Touch
  Extender) für PTZ-Kameras.

Beide Apps sprechen dasselbe Panasonic-CGI-Protokoll gegen echte Kameras und pflegten ursprünglich
je eine eigene, unabhängige Emulator-Implementierung (`tools/panasonic_emulator.py` in beiden
Repos), die jeweils eng an das interne Kamera-Katalog-Format der eigenen App gekoppelt war. Das
führte zu doppelter Pflege und tatsächlich aufgetretenem Format-Drift.

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

Fortschritt/Verifikationshistorie: siehe `CHANGELOG.md`. Beide Consumer-Apps zeigen bisher noch
nicht auf dieses Repo (TODO.md Schritt 6) — nutzen weiterhin ihre eigene
`tools/panasonic_emulator.py`-Kopie.

---

## Allgemeine Regeln

Zusammengeführt aus den Arbeitsregeln beider Quell-Repos. Wo beide Quellen dieselbe Regel mit
unterschiedlicher Betonung haben, ist hier die strengere Fassung übernommen.

### 1. Nur aus verifizierbaren Quellen arbeiten

- Vor Aussagen wie "funktioniert", "ist korrekt", "entspricht der Kamera"
  immer die Bestätigung durch PDF-Zitat, Test oder tatsächliche Ausführung
  benennen.
- Wenn etwas nicht verifiziert werden kann: sagen "nicht verifiziert" /
  "in der Spezifikation nicht definiert" statt "sollte funktionieren".

### 2. Minimal-invasiv, chirurgisch

- Kleinstmögliche gezielte Änderung statt Umbau.
- Referenzmaterial unter `reference/` nicht "nebenbei" verbessern oder
  umformatieren — es ist eine Momentaufnahme, keine lebende Codebasis.
- Bestehenden Stil im entstehenden Emulator-Code nicht ohne Auftrag ändern.

### 3. Scope strikt einhalten

- Dieses Repo baut ein Emulator-Tool — keine Reset-Sequenz-Logik, keine
  MIDI-Mapping-Logik, keine sonstigen App-spezifischen Features aus einer
  der beiden Quellen übernehmen, nur was zur Protokoll-Simulation gehört.
- Änderungen an `smart_reset_work` oder `PTZ_Control` selbst (z. B. um sie
  auf dieses Tool umzustellen) gehören nicht in dieses Repo, siehe
  `TODO.md` Abschnitt 6.

### 4. Tests zuerst und realitätsnah

- Keine Test-only-Methoden im Emulator-Code.
- Verifikation gegen echtes Verhalten (beide Apps, echte HTTP-Requests),
  nicht nur isolierte Annahmen.

### 5. Abschlussregel

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

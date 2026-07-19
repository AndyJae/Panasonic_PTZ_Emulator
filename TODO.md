# TODO — Panasonic_PTZ_Emulator

Reihenfolge ist ein Vorschlag, kein starres Gesetz — Schritte können sich je
nach Befund verschieben. Nichts hiervon ist bereits umgesetzt; dieses
Dokument ist die Ausgangsplanung nach dem Scaffolding-Schritt.

## 0. Ausgangslage (bereits recherchiert, siehe `reference/`)

Beide Quell-Emulatoren sind strukturell unterschiedlich und beide an das
Katalogformat ihrer jeweiligen App gekoppelt:

- **`reference/smart_reset_work_emulator.py`** — generischer Doppelpunkt-
  Dispatch (`O<sub>:addr:value` wird gespeichert und bei `Q<sub>:addr`
  echot), Modell-Liste kommt zur Laufzeit aus `core.registry.PluginRegistry`.
  Kennt bereits Update-Notification-Registrierung (`/cgi-bin/event`) und
  einen "externe Änderung simulieren"-Knopf, der einen echten TCP-Push im
  spec-Frame-Format schickt. Kennt **kein** Gain/Pedestal, **kein**
  ER2/ER3 (busy/out-of-range), **keine** Doppelpunkt-losen `#`-Befehle.
- **`reference/ptz_control_emulator.py`** — explizite Pro-Befehl-Behandlung
  (`QID`, `OGU`/`QGU` mit modellabhängiger Gain-Range-Prüfung → `ER1` wenn
  nicht unterstützt, `ORS`/`QRS`, Pedestal über drei verschiedene
  Kommandofamilien je nach Modell, Doppelpunkt-lose `#AXI`/`#GI`/`#R` für
  Iris). Modell-Liste kommt aus `drivers/panasonic_models/registry.py`.
  Simuliert kein Notification-Push selbst (der reale Treiber in
  `ptz_control_panasonic_aw_driver.py` parst Notifications, aber der
  Emulator sendet keine).
- **Die beiden Modell-Kataloge sind KEINE 1:1-Kopien.** PTZ_Control hat
  `drs`/`knee`/`white_clip`/`night_mode` unabhängig gegen dieselben PDFs
  geprüft und dabei echte Fehler gefunden, die in
  `reference/smart_reset_work_camera_plugins/` (Stand dieser Kopie) noch
  nicht korrigiert sind (siehe `reference/ptz_control_CLAUDE.md`, Abschnitt
  "Offene Punkte", Einträge ab "Button-Kataloge (BUTTON_FEATURES)..."). Jede
  Portierung muss das berücksichtigen, nicht blind eine der beiden Quellen
  als Wahrheit annehmen — im Zweifel `docs/specs/` direkt gegenprüfen.
- `aw_ue145.py` (smart_reset_work) vs. `aw_he145.py` (PTZ_Control, umbenannt
  nach PDF-Verifikation — "AW-UE145" existiert laut `QID`-Tabelle nicht,
  echte Modelle sind "AW-UE150"/"AW-HE145"). Modellidentität muss geklärt
  werden, bevor ein Katalogeintrag dafür übernommen wird.

## 1. Neutrales Katalogformat entwerfen

Das Emulator-Tool darf zur Laufzeit **keine** der beiden Apps importieren
(kein `core.registry`, kein `drivers.panasonic_models` — beides App-interne
Strukturen, würde eine harte Abhängigkeit erzeugen). Braucht also ein
drittes, neutrales Format pro Modell, mindestens:

- `CAMERA_ID` (+ Aliase)
- Toggle-Kommandos (on/off, optional Query, optional command-Liste statt
  Einzel-String — siehe PTZ_Controls Knee/DRS-Mehrfachkommando-Fälle)
- Trigger-Kommandos
- Dropdown-/Mehrwert-Einstellungen (Label → Kommando)
- Gain-Range + -Encoding je Modell (aus PTZ_Control, in smart_reset_work
  aktuell gar nicht abgebildet)
- Pedestal-Kommandofamilie + Range je Modell (aus PTZ_Control)
- Welche Kommandos überhaupt eine Update-Notification auslösen (aus den
  PDFs, Kap. 4/4.3.1 — Ausnahmeliste bereits in
  `reference/ptz_control_CLAUDE.md` dokumentiert)

**Offene Entscheidung:** Python-Module (wie beide Quellen) vs. deklaratives
Format (YAML/JSON) — Python ist konsistent mit beiden Vorbildern, ein
deklaratives Format wäre framework-unabhängiger und leichter diffbar/
versionierbar für ein reines Daten-Tool ohne Geschäftslogik drumherum. Vor
Schritt 2 entscheiden (mit Nutzer klären, falls nicht offensichtlich).

## 2. Modellkataloge portieren/versöhnen

- Pro Modell beide Referenzquellen (`reference/smart_reset_work_camera_plugins/*.py`,
  `reference/ptz_control_panasonic_models/*.py`) nebeneinanderlegen.
- Bei Widerspruch: `docs/specs/` direkt prüfen, nicht raten (gilt für beide
  CLAUDE.md-Vorbilder gleichermaßen als harte Regel, siehe unten).
- PTZ_Controls bereits gefundene Korrekturen (drs/knee/white_clip/
  night_mode, siehe Abschnitt 0) in den neuen Katalog übernehmen, nicht
  smart_reset_works unkorrigierte Version.
- `aw_ue145`/`aw_he145`-Frage klären, bevor dieser Eintrag portiert wird.

## 3. Generische Dispatch-Engine zusammenführen

- Doppelpunkt-Logik (`O<sub>:addr:value` / `Q<sub>:addr`) aus
  smart_reset_work übernehmen — bleibt weiterhin die Grundlage, da generisch
  und modellunabhängig.
- Doppelpunkt-lose `#AXI`/`#GI`/`#R`-Behandlung aus PTZ_Control übernehmen
  (für Iris/PTZ-Steuerung).
- Gain/Pedestal-Simulation aus PTZ_Control übernehmen (modellabhängige
  Range-Prüfung, Kommandofamilie je Modell).

## 4. Fehlende Funktionalität ergänzen, die KEINE der beiden Quellen hat

- **ER2 (busy)/ER3 (out-of-range) simulieren** — beide Quellen akzeptieren
  aktuell jeden syntaktisch erkannten Befehl unabhängig vom Wertebereich;
  das ist eine bekannte, in beiden CLAUDE.md-Dateien dokumentierte Lücke.
- **Update-Notification-Push für JEDE Kommandoänderung**, nicht nur für den
  manuellen "simulate change"-Knopf — d. h. wenn Gain/Pedestal/Dropdown über
  die Emulator-UI direkt gesetzt werden, sollte optional automatisch auch
  gepusht werden (aktuell nur bei explizitem "simulate external change").

## 5. Control-UI zusammenführen

Ausgangspunkt `reference/smart_reset_work_emulator.py`s UI (Modell/Port-
Auswahl, Log, "externe Änderung simulieren"), ergänzt um
`reference/ptz_control_emulator.py`s Zustandsanzeige (Iris/Gain/Pedestal/
ND/Bars) und modellabhängige Steuerelemente.

## 6. Beide Apps umstellen (separate PRs, außerhalb dieses Repos)

- `smart_reset_work` (bzw. die veröffentlichte `smart-reset-browser`-Kopie)
  und `PTZ_Control` jeweils in einem eigenen Schritt auf das neue Tool
  umstellen, ihre eigenen `tools/panasonic_emulator.py` erst entfernen,
  wenn das neue Tool nachweislich alle bisher genutzten Testfälle abdeckt.
- Nicht in diesem Repo erledigen — Änderungen an fremden Repos brauchen
  eigene Reviews dort.

## 7. Tests

- Mindestens: Dispatch-Logik (Doppelpunkt + doppelpunktlos), Katalog-
  Auflösung pro Modell, Notification-Frame-Encoding/-Parsing.
- Realitätsnah gegen beide Apps verifizieren (Connect/Reset/Feature-Toggle/
  Notification-Flow), nicht nur isolierte Unit-Tests — deckt sich mit
  PTZ_Controls "Tests zuerst und realitätsnah"-Regel (siehe CLAUDE.md).

"""emulator/models/aw_he145.py -- Panasonic AW-HE145.

CAMERA_ID ist "AW-HE145" (nicht "AW-UE145"), siehe
`reference/ptz_control_panasonic_models/aw_he145.py`s Docstring: das
dedizierte `docs/specs/AW-UE150HE145_InterfaceSpecification_E.pdf` zeigt in
seiner "Model Number"-Tabelle zwei unterschiedliche echte QID-Antworten,
`OID:AW-UE150` und `OID:AW-HE145`, fuer zwei verschiedene Modelle im selben
Dokument -- "AW-UE145" (smart_reset_works Dateiname) passt zu keinem der
beiden. "AW-UE145" bleibt als Alias erhalten.

Feature-Katalog identisch zu AW-UE150A (von dort importiert, wie in
ptz_control_panasonic_models/aw_he145.py). Eigene Gain-Werte laut o. g. PDF
(gilt fuer AW-UE150 UND AW-HE145 gemeinsam, keine "only supported by"-
Einschraenkung im Gain-Abschnitt) -- zufaellig identisch zu AW-UE150As
bereits korrigierten Werten.
"""

from emulator.models.aw_ue150 import FEATURES, FEATURE_LABELS  # noqa: F401

CAMERA_ID = "AW-HE145"
CAMERA_ID_ALIASES = ["AW-UE145", "AW-UE150HE", "AW-UE150HE145"]
DISPLAY_NAME = "Panasonic AW-HE145"

GAIN_MIN_DB = -3
GAIN_MAX_DB = 42
GAIN_STEP_DB = 1

PEDESTAL_COMMAND = "OSJ:0F"
PEDESTAL_QUERY_COMMAND = "QSJ:0F"
PEDESTAL_MIN = -200
PEDESTAL_MAX = 200
PEDESTAL_CENTER_DATA = 0x800
PEDESTAL_SCALE = 1
PEDESTAL_DATA_WIDTH = 3

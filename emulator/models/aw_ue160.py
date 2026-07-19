"""emulator/models/aw_ue160.py -- Panasonic AW-UE160.

Toggle/Trigger-Kommandos aus `reference/ptz_control_panasonic_models/
aw_ue160.py`s BUTTON_FEATURES uebernommen (PDF-verifiziert, siehe dortiger
Docstring). Dropdown-Kommandos (color_temp/gamma_curve/linear_matrix_table/
matrix_preset) zusaetzlich aus `reference/smart_reset_work_camera_plugins/
aw_ue160.py`s UI_DROPDOWNS uebernommen -- dort keine Entsprechung in
BUTTON_FEATURES.

**Bewusste Umbenennung (Namenskollision, siehe TODO.md/Plan):** AW-UE160
hat sowohl einen `gamma`-Toggle (OSA:0A, schaltet Gamma-Verarbeitung an/aus)
als auch ein `gamma`-Preset-Dropdown (OSJ:D7, waehlt die Gamma-Kurve) sowie
analog `linear_matrix` (Toggle OSL:6C) vs. Tabellenwahl (OSA:00). Die
Toggle-Keys behalten ihren Namen (deckungsgleich mit ptz_control), die
Dropdown-Keys wurden zu `gamma_curve` bzw. `linear_matrix_table` umbenannt --
nur bei diesem Modell noetig, sonst keine Kollision in der Modell-Matrix.

`knee_manual`/`knee_auto` bewusst ohne `query`: das Zusammenspiel von
`OSL:45` (schaltet Knee ueberhaupt scharf) und `OSA:2D` (Manual/Auto) beim
Auslesen ist in keiner lokalen PDF dokumentiert (siehe ptz_control-Quelle).
"""

CAMERA_ID = "AW-UE160"
DISPLAY_NAME = "Panasonic AW-UE160"

GAIN_MIN_DB = -6
GAIN_MAX_DB = 12
GAIN_STEP_DB = 1

PEDESTAL_COMMAND = "OSJ:0F"
PEDESTAL_QUERY_COMMAND = "QSJ:0F"
PEDESTAL_MIN = -200
PEDESTAL_MAX = 200
PEDESTAL_CENTER_DATA = 0x800
PEDESTAL_SCALE = 1
PEDESTAL_DATA_WIDTH = 3

FEATURES: dict[str, dict] = {
    "auto_focus": {"kind": "toggle", "on": "OAF:1", "off": "OAF:0", "query": "QAF", "query_on_value": "1"},
    "auto_iris": {"kind": "toggle", "on": "ORS:1", "off": "ORS:0"},
    "awb_black": {"kind": "trigger", "cmd": "OAS"},
    "aww_white": {"kind": "trigger", "cmd": "OWS"},
    "drs": {"kind": "toggle", "on": "OSA:0D:1", "off": "OSA:0D:0", "query": "QSA:0D", "query_on_value": "1"},
    "flare": {"kind": "toggle", "on": "OSA:11:1", "off": "OSA:11:0", "query": "QSA:11", "query_on_value": "1"},
    "gamma": {"kind": "toggle", "on": "OSA:0A:1", "off": "OSA:0A:0", "query": "QSA:0A", "query_on_value": "1"},
    "knee_manual": {"kind": "toggle", "on": ["OSL:45:1", "OSA:2D:1"], "off": "OSL:45:0"},
    "knee_auto": {"kind": "toggle", "on": ["OSL:45:1", "OSA:2D:2"], "off": "OSL:45:0"},
    "linear_matrix": {"kind": "toggle", "on": "OSL:6C:1", "off": "OSL:6C:0", "query": "QSL:6C", "query_on_value": "1"},
    "matrix": {"kind": "toggle", "on": "OSA:84:1", "off": "OSA:84:0", "query": "QSA:84", "query_on_value": "1"},
    "osd": {"kind": "toggle", "on": "DUS:1", "off": "DUS:0", "query": "QUS", "query_on_value": "1"},
    "white_clip": {"kind": "toggle", "on": "OSA:2E:1", "off": "OSA:2E:0", "query": "QSA:2E", "query_on_value": "1"},
    "color_temp": {"kind": "dropdown", "query": "QAW", "options": [
        ("White Balance is AWC A", "OAW:1"),
        ("White Balance is AWC B", "OAW:2"),
        ("White Balance is Preset 3200K", "OAW:4"),
        ("White Balance is Preset 5600K", "OAW:5"),
        ("White Balance is VAR", "OAW:9"),
        ("White Balance is ATW", "OAW:0"),
    ]},
    "gamma_curve": {"kind": "dropdown", "query": "QSJ:D7", "options": [
        ("Gamma is HD", "OSJ:D7:00"),
        ("Gamma is Normal", "OSJ:D7:01"),
        ("Gamma is Cinema 1", "OSJ:D7:02"),
        ("Gamma is Cinema 2", "OSJ:D7:03"),
    ]},
    "linear_matrix_table": {"kind": "dropdown", "query": "QSA:00", "options": [
        ("Linear Matrix Table is A", "OSA:00:0"),
        ("Linear Matrix Table is B", "OSA:00:1"),
    ]},
    "matrix_preset": {"kind": "dropdown", "query": "QSE:31", "options": [
        ("Matrix Preset is Normal", "OSE:31:0"),
        ("Matrix Preset is Cinema1", "OSE:31:1"),
        ("Matrix Preset is Cinema2", "OSE:31:2"),
        ("Matrix Preset is User", "OSE:31:3"),
        ("Matrix Preset is HD", "OSE:31:4"),
    ]},
}

FEATURE_LABELS: dict[str, str] = {
    "auto_focus": "Auto Focus",
    "auto_iris": "Auto Iris",
    "drs": "DRS",
    "flare": "Flare",
    "gamma": "Gamma",
    "knee_manual": "Knee: Manual",
    "knee_auto": "Knee: Auto",
    "linear_matrix": "Linear Matrix",
    "matrix": "Matrix",
    "osd": "OSD",
    "white_clip": "White Clip",
    "awb_black": "ABB (Black)",
    "aww_white": "AWW (White)",
    "color_temp": "White Balance Source",
    "gamma_curve": "Gamma Curve",
    "linear_matrix_table": "Linear Matrix Table",
    "matrix_preset": "Matrix Preset",
}

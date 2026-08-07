"""emulator/models/aw_ue80.py -- Panasonic AW-UE80.

Keine CAMERA_ID_ALIASES -- die verwandten Modelle UE30/UE40/UE50 sind
eigene, sehr kleine Re-Export-Module (siehe aw_ue30.py/aw_ue40.py/
aw_ue50.py).

Toggle/Trigger-Kommandos aus `reference/ptz_control_panasonic_models/
aw_ue80.py`s BUTTON_FEATURES (PDF-korrigiert: drs in drs_low/mid/high).
Dropdown-Kommandos (color_temp/gamma) zusaetzlich aus
`reference/smart_reset_work_camera_plugins/aw_ue80.py`s UI_DROPDOWNS.

Bewusst KEIN `knee`-Feature: die dedizierte PDF (AW-UE80UE50UE40_
InterfaceSpecification_E.pdf) bestaetigt zwar in Kap. 8, dass ein
"Knee mode OSA:2D"-Menu existiert, die genaue Werte-/Label-Tabelle in Kap. 9
liess sich beim Verifizieren nicht sauber extrahieren -- offener Punkt in
`reference/ptz_control_CLAUDE.md`, hier bewusst nicht ergaenzt (kein
erfundener Wert).
"""

CAMERA_ID = "AW-UE80"
DISPLAY_NAME = "Panasonic AW-UE80"

GAIN_MIN_DB = 0
GAIN_MAX_DB = 42
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
    "drs_low": {"kind": "toggle", "on": "OSE:33:1", "off": "OSE:33:0", "query": "QSE:33", "query_on_value": "1"},
    "drs_mid": {"kind": "toggle", "on": "OSE:33:2", "off": "OSE:33:0", "query": "QSE:33", "query_on_value": "2"},
    "drs_high": {"kind": "toggle", "on": "OSE:33:3", "off": "OSE:33:0", "query": "QSE:33", "query_on_value": "3"},
    "osd": {"kind": "toggle", "on": "DUS:1", "off": "DUS:0", "query": "QUS", "query_on_value": "1"},
    "white_clip": {"kind": "toggle", "on": "OSA:2E:1", "off": "OSA:2E:0", "query": "QSA:2E", "query_on_value": "1"},
    "color_temp": {"kind": "dropdown", "query": "QAW", "options": [
        ("White Balance is AWB A", "OAW:1"),
        ("White Balance is AWB B", "OAW:2"),
        ("White Balance is Preset 3200K", "OAW:4"),
        ("White Balance is Preset 5600K", "OAW:5"),
        ("White Balance is VAR", "OAW:9"),
        ("White Balance is ATW", "OAW:0"),
    ]},
    "gamma": {"kind": "dropdown", "query": "QSJ:D7", "options": [
        ("Gamma is HD", "OSJ:D7:00"),
        ("Gamma is Normal", "OSJ:D7:01"),
        ("Gamma is Cinema 1", "OSJ:D7:02"),
        ("Gamma is Cinema 2", "OSJ:D7:03"),
        ("Gamma is Still Like", "OSJ:D7:04"),
    ]},
    "adaptive_matrix": {"kind": "toggle", "on": "OSJ:4F:1", "off": "OSJ:4F:0", "query": "QSJ:4F", "query_on_value": "1"},
    "matrix_type": {"kind": "dropdown", "query": "QSE:31", "options": [
        ("Matrix Type is Normal", "OSE:31:0"),
        ("Matrix Type is EBU", "OSE:31:1"),
        ("Matrix Type is NTSC", "OSE:31:2"),
        ("Matrix Type is User", "OSE:31:3"),
    ]},
}

FEATURE_LABELS: dict[str, str] = {
    "auto_focus": "Auto Focus",
    "auto_iris": "Auto Iris",
    "drs_low": "DRS: Low",
    "drs_mid": "DRS: Mid",
    "drs_high": "DRS: High",
    "osd": "OSD",
    "white_clip": "White Clip",
    "awb_black": "ABB (Black)",
    "aww_white": "AWW (White)",
    "color_temp": "White Balance Source",
    "gamma": "Gamma",
    "adaptive_matrix": "Adaptive Matrix",
    "matrix_type": "Matrix Type",
}

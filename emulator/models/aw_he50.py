"""emulator/models/aw_he50.py -- Panasonic AW-HE50 series.

Toggle/Trigger-Kommandos aus `reference/ptz_control_panasonic_models/
aw_he50.py`s BUTTON_FEATURES (PDF-korrigiert: kein white_clip, `drs` nur
2 Werte drs_low/drs_high). Dropdown-Kommandos (color_temp, nur 3 Optionen --
einfachste color_temp-Auswahl aller Modelle) zusaetzlich aus
`reference/smart_reset_work_camera_plugins/aw_he50.py`s UI_DROPDOWNS.
Kein `gamma`-Dropdown in der Quelle (aelteres, einfacheres Modell als
HE120/HE130).
"""

CAMERA_ID = "AW-HE50"
CAMERA_ID_ALIASES = ["AW-HE50H", "AW-HE50E", "AW-HE50S"]
DISPLAY_NAME = "Panasonic AW-HE50"

GAIN_MIN_DB = 0
GAIN_MAX_DB = 18
GAIN_STEP_DB = 3

PEDESTAL_COMMAND = "OTP"
PEDESTAL_QUERY_COMMAND = "QTP"
PEDESTAL_MIN = -10
PEDESTAL_MAX = 10
PEDESTAL_CENTER_DATA = 0x96
PEDESTAL_SCALE = 15
PEDESTAL_DATA_WIDTH = 3

FEATURES: dict[str, dict] = {
    "auto_focus": {"kind": "toggle", "on": "OAF:1", "off": "OAF:0", "query": "QAF", "query_on_value": "1"},
    "auto_iris": {"kind": "toggle", "on": "ORS:1", "off": "ORS:0"},
    "awb_black": {"kind": "trigger", "cmd": "OAS"},
    "aww_white": {"kind": "trigger", "cmd": "OWS"},
    "drs_low": {"kind": "toggle", "on": "OSE:33:1", "off": "OSE:33:0", "query": "QSE:33", "query_on_value": "1"},
    "drs_high": {"kind": "toggle", "on": "OSE:33:3", "off": "OSE:33:0", "query": "QSE:33", "query_on_value": "3"},
    "osd": {"kind": "toggle", "on": "DUS:1", "off": "DUS:0", "query": "QUS", "query_on_value": "1"},
    "color_temp": {"kind": "dropdown", "query": "QAW", "options": [
        ("White Balance is AWB A", "OAW:1"),
        ("White Balance is AWB B", "OAW:2"),
        ("White Balance is ATW", "OAW:0"),
    ]},
}

FEATURE_LABELS: dict[str, str] = {
    "auto_focus": "Auto Focus",
    "auto_iris": "Auto Iris",
    "drs_low": "DRS: Low",
    "drs_high": "DRS: High",
    "osd": "OSD",
    "awb_black": "ABB (Black)",
    "aww_white": "AWW (White)",
    "color_temp": "White Balance Source",
}

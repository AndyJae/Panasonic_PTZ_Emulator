"""emulator/models/aw_he120.py -- Panasonic AW-HE120.

Toggle/Trigger-Kommandos aus `reference/ptz_control_panasonic_models/
aw_he120.py`s BUTTON_FEATURES (PDF-korrigiert: kein `knee`, kein
`white_clip` -- Spec nennt AW-HE120 in keiner der beiden "only supported
by"-Listen; `drs` in drs_low/mid/high zerlegt). Dropdown-Kommandos
(color_temp/gamma) zusaetzlich aus
`reference/smart_reset_work_camera_plugins/aw_he120.py`s UI_DROPDOWNS.
"""

CAMERA_ID = "AW-HE120"
CAMERA_ID_ALIASES = ["AW-HE125", "AW-HE120W", "AW-HE120K"]
DISPLAY_NAME = "Panasonic AW-HE120"

GAIN_MIN_DB = 0
GAIN_MAX_DB = 18
GAIN_STEP_DB = 1

PEDESTAL_COMMAND = "OTP"
PEDESTAL_QUERY_COMMAND = "QTP"
PEDESTAL_MIN = -150
PEDESTAL_MAX = 150
PEDESTAL_CENTER_DATA = 0x96
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
    "color_temp": {"kind": "dropdown", "query": "QAW", "options": [
        ("White Balance is AWB A", "OAW:1"),
        ("White Balance is AWB B", "OAW:2"),
        ("White Balance is Preset 3200K", "OAW:4"),
        ("White Balance is Preset 5600K", "OAW:5"),
        ("White Balance is VAR", "OAW:9"),
        ("White Balance is ATW", "OAW:0"),
    ]},
    "gamma": {"kind": "dropdown", "query": "QSE:72", "options": [
        ("Gamma is Off", "OSE:72:0"),
        ("Gamma is Normal", "OSE:72:1"),
        ("Gamma is Cinema", "OSE:72:2"),
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
    "awb_black": "ABB (Black)",
    "aww_white": "AWW (White)",
    "color_temp": "White Balance Source",
    "gamma": "Gamma",
    "adaptive_matrix": "Adaptive Matrix",
    "matrix_type": "Matrix Type",
}

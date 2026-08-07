"""emulator/models/aw_ue100.py -- Panasonic AW-UE100.

Keine CAMERA_ID_ALIASES in beiden Referenzquellen.

Toggle/Trigger-Kommandos aus `reference/ptz_control_panasonic_models/
aw_ue100.py`s BUTTON_FEATURES (PDF-korrigiert gegen das dedizierte
AW-UE100_InterfaceSpecification_E.pdf: drs in drs_low/mid/high, knee in
knee_manual/knee_auto). Dropdown-Kommandos (color_temp/gamma) zusaetzlich
aus `reference/smart_reset_work_camera_plugins/aw_ue100.py`s UI_DROPDOWNS
(dort mit "AWC A/B"-Wortlaut statt "AWB A/B", 1:1 uebernommen).

Gain-Maximalwert (42dB) ist an "Super Gain" gekoppelt (36dB wenn aus) --
Kopplung hier wie in ptz_control nicht durchgesetzt (kein FullAuto-/
Super-Gain-Zustand im Emulator simuliert).
"""

CAMERA_ID = "AW-UE100"
DISPLAY_NAME = "Panasonic AW-UE100"

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
    "knee_manual": {"kind": "toggle", "on": "OSA:2D:1", "off": "OSA:2D:0", "query": "QSA:2D", "query_on_value": "1"},
    "knee_auto": {"kind": "toggle", "on": "OSA:2D:2", "off": "OSA:2D:0", "query": "QSA:2D", "query_on_value": "2"},
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
    "gamma": {"kind": "dropdown", "query": "QSE:72", "options": [
        ("Gamma is HD", "OSE:72:0"),
        ("Gamma is FILMLIKE 1", "OSE:72:2"),
        ("Gamma is FILMLIKE 2", "OSE:72:3"),
        ("Gamma is FILMLIKE 3", "OSE:72:4"),
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
    "knee_manual": "Knee: Manual",
    "knee_auto": "Knee: Auto",
    "osd": "OSD",
    "white_clip": "White Clip",
    "awb_black": "ABB (Black)",
    "aww_white": "AWW (White)",
    "color_temp": "White Balance Source",
    "gamma": "Gamma",
    "adaptive_matrix": "Adaptive Matrix",
    "matrix_type": "Matrix Type",
}

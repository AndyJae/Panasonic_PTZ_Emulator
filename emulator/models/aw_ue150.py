"""emulator/models/aw_ue150.py -- Panasonic AW-UE150A.

CAMERA_ID ist "AW-UE150A" (nicht "AW-UE150") -- so in beiden Referenzquellen
gefuehrt, "AW-UE150" ist dort ein Alias, keine Tippabweichung.

Toggle/Trigger-Kommandos aus `reference/ptz_control_panasonic_models/
aw_ue150.py`s BUTTON_FEATURES (PDF-korrigiert: Gain -3..+42dB laut zwei
neueren dedizierten PDFs statt 0..+42dB aus dem aelteren Multi-Modell-PDF,
drs/knee in Einzel-Zielzustand-Toggles zerlegt). Dropdown-Kommandos
(color_temp/gamma_mode/matrix_type) zusaetzlich aus
`reference/smart_reset_work_camera_plugins/aw_ue150.py`s UI_DROPDOWNS
uebernommen -- keine Namenskollision mit den Toggle-Keys bei diesem Modell
(kein "matrix"- oder "gamma"-Toggle vorhanden, nur "adaptive_matrix").

color_temp-Platzhaltereintrag ("Select White Balance Mode", cmd=None) aus
der Quelle bewusst NICHT uebernommen -- kein sendbares Kommando, nur
UI-Hinweistext.
"""

CAMERA_ID = "AW-UE150A"
CAMERA_ID_ALIASES = ["AW-UE150", "AW-UE155", "AW-UN145"]
DISPLAY_NAME = "Panasonic AW-UE150A"

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

FEATURES: dict[str, dict] = {
    "adaptive_matrix": {"kind": "toggle", "on": "OSJ:4F:1", "off": "OSJ:4F:0", "query": "QSJ:4F", "query_on_value": "1"},
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
        ("White Balance is ATW", "OAW:0"),
        ("White Balance is AWC A", "OAW:1"),
        ("White Balance is AWC B", "OAW:2"),
        ("White Balance is Preset 3200K", "OAW:4"),
        ("White Balance is Preset 5600K", "OAW:5"),
        ("White Balance is VAR", "OAW:9"),
    ]},
    "gamma_mode": {"kind": "dropdown", "query": "QSE:72", "options": [
        ("Gamma Mode is HD", "OSE:72:0"),
        ("Gamma Mode is FILMLIKE1", "OSE:72:2"),
        ("Gamma Mode is FILMLIKE2", "OSE:72:3"),
        ("Gamma Mode is FILMLIKE3", "OSE:72:4"),
        ("Gamma Mode is FILM REC", "OSE:72:5"),
        ("Gamma Mode is VIDEO REC", "OSE:72:6"),
    ]},
    "matrix_type": {"kind": "dropdown", "query": "QSE:31", "options": [
        ("Matrix Type is Normal", "OSE:31:0"),
        ("Matrix Type is EBU", "OSE:31:1"),
        ("Matrix Type is NTSC", "OSE:31:2"),
        ("Matrix Type is User", "OSE:31:3"),
    ]},
}

FEATURE_LABELS: dict[str, str] = {
    "adaptive_matrix": "Adaptive Matrix",
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
    "gamma_mode": "Gamma Mode",
    "matrix_type": "Matrix Type",
}

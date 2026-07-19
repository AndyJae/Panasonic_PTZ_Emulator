"""emulator/models/aw_he40.py -- Panasonic AW-HE40 series.

Covers: AW-HE40, AW-HE65, AW-HE70, AW-HE48, AW-HE58, AW-HE35, AW-HE38,
AW-HN38/40/65/70 (Aliase, deckungsgleich zwischen beiden Referenzquellen
und der bitfocus-Kommandomatrix -- siehe
reference/bitfocus_companion_panasonic_models_matrix.md).

Toggle/Trigger-Kommandos aus `reference/ptz_control_panasonic_models/
aw_he40.py`s BUTTON_FEATURES (PDF-korrigiert: kein white_clip, `drs` nur
2 Werte drs_low/drs_high -- Data-Wert 2 nicht belegt --, `night_mode` ueber
OSD:B2 statt des urspruenglich falschen OSI:1A). Dropdown-Kommandos
(color_temp/gamma) zusaetzlich aus
`reference/smart_reset_work_camera_plugins/aw_he40.py`s UI_DROPDOWNS.

`night_mode` ist ptz_control-exklusiv -- im aktuellen smart_reset_work-
Quellstand nicht vorhanden (dessen Docstring behauptet eine Herkunft von
dort, die beim Nachpruefen nicht zutrifft, siehe Modell-Diff-Analyse).
"""

CAMERA_ID = "AW-HE40"
CAMERA_ID_ALIASES = [
    "AW-HE40S", "AW-HE40W", "AW-HE40HE",
    "AW-HE65", "AW-HE65H", "AW-HE65E",
    "AW-HE70", "AW-HE70HE",
    "AW-HE48", "AW-HE58",
    "AW-HE35", "AW-HE38",
    "AW-HN38", "AW-HN40", "AW-HN65", "AW-HN70",
]
DISPLAY_NAME = "Panasonic AW-HE40"

GAIN_MIN_DB = 0
GAIN_MAX_DB = 48
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
    "night_mode": {"kind": "toggle", "on": "OSD:B2:1", "off": "OSD:B2:0", "query": "QSD:B2", "query_on_value": "1"},
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
}

FEATURE_LABELS: dict[str, str] = {
    "auto_focus": "Auto Focus",
    "auto_iris": "Auto Iris",
    "drs_low": "DRS: Low",
    "drs_high": "DRS: High",
    "osd": "OSD",
    "awb_black": "ABB (Black)",
    "aww_white": "AWW (White)",
    "night_mode": "Night Mode",
    "color_temp": "White Balance Source",
    "gamma": "Gamma",
}

"""emulator/models/ak_ub300.py -- Panasonic AK-UB300.

Toggle/Trigger-Kommandos aus `reference/ptz_control_panasonic_models/
ak_ub300.py`s BUTTON_FEATURES (PDF-korrigiert: kein white_clip, `drs`
bewusst nicht in drs_low/high/mid zerlegt -- PDF nennt AK-UB300 in keiner
der beiden DRS-Wertegruppen, weder Bestaetigung noch Widerspruch). Dropdown-
Kommandos (color_temp/gamma/gain_select) zusaetzlich aus
`reference/smart_reset_work_camera_plugins/ak_ub300.py`s UI_DROPDOWNS.

Bewusst KEIN GAIN_MIN_DB/GAIN_MAX_DB: AK-UB300 nutzt `OGS:01` (Bereichswahl
LOW/MID/HIGH, hier als `gain_select`-Dropdown abgebildet) + `OSA:50/51/52`
(dB je Bereich) statt eines einfachen `OGU`-Encoder-Bereichs -- strukturell
inkompatibel mit dem Gain-Dispatch der anderen Modelle (siehe
dispatch.py). `OGU` liefert fuer dieses Modell daher ER1, wie bei einer
echten Kamera ohne dieses Kommando.
"""

CAMERA_ID = "AK-UB300"
CAMERA_ID_ALIASES = ["AK-UB300GJ", "AK-UB300EJ"]
DISPLAY_NAME = "Panasonic AK-UB300"

PEDESTAL_COMMAND = "OSG:4A"
PEDESTAL_QUERY_COMMAND = "QSG:4A"
PEDESTAL_MIN = -99
PEDESTAL_MAX = 99
PEDESTAL_CENTER_DATA = 0x80
PEDESTAL_SCALE = 1
PEDESTAL_DATA_WIDTH = 2

FEATURES: dict[str, dict] = {
    "auto_iris": {"kind": "toggle", "on": "ORS:1", "off": "ORS:0"},
    "awb_black": {"kind": "trigger", "cmd": "OAS"},
    "aww_white": {"kind": "trigger", "cmd": "OWS"},
    "drs": {"kind": "toggle", "on": "OSE:33:1", "off": "OSE:33:0"},
    "knee_manual": {"kind": "toggle", "on": "OSA:2D:1", "off": "OSA:2D:0", "query": "QSA:2D", "query_on_value": "1"},
    "knee_auto": {"kind": "toggle", "on": "OSA:2D:2", "off": "OSA:2D:0", "query": "QSA:2D", "query_on_value": "2"},
    "super_gain": {"kind": "toggle", "on": "OSI:28:1", "off": "OSI:28:0"},
    "osd": {"kind": "toggle", "on": "DUS:1", "off": "DUS:0", "query": "QUS", "query_on_value": "1"},
    "color_temp": {"kind": "dropdown", "query": "QAW", "options": [
        ("White Balance is AWB A", "OAW:1"),
        ("White Balance is AWB B", "OAW:2"),
        ("White Balance is Preset 3200K", "OAW:4"),
        ("White Balance is Preset 5600K", "OAW:5"),
        ("White Balance is VAR", "OAW:9"),
        ("White Balance is ATW", "OAW:0"),
    ]},
    "gamma": {"kind": "dropdown", "query": "QSG:86", "options": [
        ("Gamma is HD", "OSG:86:0"),
        ("Gamma is FILMLIKE 1", "OSG:86:1"),
        ("Gamma is FILMLIKE 2", "OSG:86:2"),
        ("Gamma is FILMLIKE 3", "OSG:86:3"),
        ("Gamma is FILM REC", "OSG:86:4"),
        ("Gamma is VIDEO REC", "OSG:86:5"),
    ]},
    "gain_select": {"kind": "dropdown", "query": "QGS:01", "options": [
        ("Gain Region is LOW", "OGS:01:0"),
        ("Gain Region is MID", "OGS:01:1"),
        ("Gain Region is HIGH", "OGS:01:2"),
    ]},
}

FEATURE_LABELS: dict[str, str] = {
    "auto_iris": "Auto Iris",
    "drs": "DRS",
    "knee_manual": "Knee: Manual",
    "knee_auto": "Knee: Auto",
    "awb_black": "ABB (Black)",
    "aww_white": "AWW (White)",
    "super_gain": "Super Gain",
    "osd": "OSD",
    "color_temp": "White Balance Source",
    "gamma": "Gamma",
    "gain_select": "Gain Region",
}

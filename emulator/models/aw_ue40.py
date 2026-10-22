"""emulator/models/aw_ue40.py -- Panasonic AW-UE40.

Gleicher Befehlssatz wie AW-UE80 (siehe aw_ue80.py) -- nur CAMERA_ID/
DISPLAY_NAME unterscheiden sich, analog zu beiden Referenzquellen.
"""

from emulator.models.aw_ue80 import (  # noqa: F401
    FEATURES,
    FEATURE_LABELS,
    GAIN_MAX_DB,
    GAIN_MIN_DB,
    GAIN_STEP_DB,
    PEDESTAL_CENTER_DATA,
    PEDESTAL_COMMAND,
    PEDESTAL_DATA_WIDTH,
    PEDESTAL_MAX,
    PEDESTAL_MIN,
    PEDESTAL_QUERY_COMMAND,
    PEDESTAL_SCALE,
)

CAMERA_ID = "AW-UE40"
DISPLAY_NAME = "Panasonic AW-UE40"

# OSD Mix (OSE:7B/QSE:7B, Bitmaske) -- simulierte Ausgaenge (Label, Bit).
# Quelle: AW-UE80UE50UE40_InterfaceSpecification_E.pdf, UE40-Liste.
OSD_MIX_OUTPUTS = [
    ("HDMI", 0x02),
    ("IP/NDI|HX", 0x10),
]

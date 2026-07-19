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

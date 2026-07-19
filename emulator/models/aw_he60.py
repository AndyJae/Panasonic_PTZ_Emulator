"""emulator/models/aw_he60.py -- Panasonic AW-HE60 series.

Gleicher Befehlssatz wie AW-HE50 (siehe aw_he50.py) -- nur CAMERA_ID/
CAMERA_ID_ALIASES/DISPLAY_NAME unterscheiden sich, analog zu beiden
Referenzquellen.
"""

from emulator.models.aw_he50 import (  # noqa: F401
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

CAMERA_ID = "AW-HE60"
CAMERA_ID_ALIASES = ["AW-HE60H", "AW-HE60E", "AW-HE60S"]
DISPLAY_NAME = "Panasonic AW-HE60"

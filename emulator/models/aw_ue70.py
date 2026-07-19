"""emulator/models/aw_ue70.py -- Panasonic AW-UE70 series.

Trotz "UE"-Namen ein reiner Re-Export von AW-HE40 (nicht AW-UE80) auf beiden
Referenzquellen -- teilt Gain (0-48dB, 3dB-Schritte) und OTP-Pedestal-Familie
mit der HE40-Gruppe, nicht die OSJ:0F-Familie der anderen UE-Modelle.
"""

from emulator.models.aw_he40 import (  # noqa: F401
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

CAMERA_ID = "AW-UE70"
CAMERA_ID_ALIASES = ["AW-UN70", "AW-UE65", "AW-UE63"]
DISPLAY_NAME = "Panasonic AW-UE70"

"""Tests fuer emulator/dispatch.py -- Doppelpunkt + doppelpunktlos, Gain/
Pedestal-ER3, Cross-Modell-ER1, generischer Fallback, ER2-Hebel,
Notification-Push (inkl. Kap.-4.3.1-Ausnahmen)."""

from emulator import dispatch
from emulator.state import CameraState


def _state(model_id: str = "AW-UE160") -> CameraState:
    return CameraState(model_id)


def test_empty_command_returns_er1():
    assert dispatch.handle_command(_state(), "") == "ER1:00"


def test_qid_returns_model_id():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "QID") == "OID:AW-UE160"


def test_gain_set_and_query_roundtrip():
    s = _state("AW-UE160")  # -6..12dB
    assert dispatch.handle_command(s, "OGU:0E") == "OGU:0E"  # +6dB
    assert dispatch.handle_command(s, "QGU") == "OGU:0E"


def test_gain_out_of_range_returns_er3():
    s = _state("AW-UE160")  # max +12dB -> data 0x14
    assert dispatch.handle_command(s, "OGU:1C") == "ER3:OGU:1C"  # +20dB, zu hoch


def test_gain_agc_accepted_unconditionally():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "OGU:80") == "OGU:80"


def test_pedestal_set_and_query_roundtrip():
    s = _state("AW-UE160")  # OSJ:0F, -200..200, center 0x800
    assert dispatch.handle_command(s, "OSJ:0F:850") == "OSJ:0F:850"
    assert dispatch.handle_command(s, "QSJ:0F") == "OSJ:0F:850"


def test_pedestal_out_of_range_returns_er3():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "OSJ:0F:900") == "ER3:OSJ:0F:900"  # +256, außerhalb -200..200


def test_pedestal_cross_family_returns_er1():
    # AW-UE160 nutzt OSJ:0F, nicht OTP -- OTP ist die Pedestal-Familie von
    # HE50/HE60/HE120/HE130/HR140/HE40/HE42/UE70.
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "QTP") == "ER1:QTP"
    assert dispatch.handle_command(s, "OTP:096") == "ER1:OTP:096"




def test_toggle_feature_set_and_query():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "OAF:1") == "OAF:1"
    assert dispatch.handle_command(s, "QAF") == "OAF:1"
    assert dispatch.handle_command(s, "OAF:0") == "OAF:0"
    assert dispatch.handle_command(s, "QAF") == "OAF:0"


def test_dropdown_feature_set_and_query():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "OAW:1") == "OAW:1"
    assert dispatch.handle_command(s, "QAW") == "OAW:1"


def test_ue160_gamma_toggle_and_gamma_curve_dropdown_dont_collide():
    """Regressionstest fuer die bewusste Umbenennung (gamma-Toggle vs.
    gamma_curve-Dropdown, siehe emulator/models/aw_ue160.py)."""
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "OSA:0A:1") == "OSA:0A:1"  # Toggle an
    assert dispatch.handle_command(s, "OSJ:D7:02") == "OSJ:D7:02"  # Kurve waehlen
    assert dispatch.handle_command(s, "QSA:0A") == "OSA:0A:1"  # Toggle unveraendert
    assert dispatch.handle_command(s, "QSJ:D7") == "OSJ:D7:02"  # Kurve unveraendert


def test_cross_model_gate_rejects_unsupported_feature():
    # knee_auto (OSA:2D:2) existiert bei HE130/HR140/UE100/UE150A/UE160,
    # aber nicht bei HE50.
    s = _state("AW-HE50")
    assert dispatch.handle_command(s, "OSA:2D:2") == "ER1:OSA:2D:2"


def test_cross_model_gate_rejects_unsupported_query():
    s = _state("AW-HE40")  # kein knee-Feature ueberhaupt
    assert dispatch.handle_command(s, "QSA:2D") == "ER1:QSA:2D"


def test_generic_fallback_accepts_and_echoes_unlisted_command():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "OSA:22:80") == "OSA:22:80"  # Knee R Point, nicht katalogisiert
    assert dispatch.handle_command(s, "QSA:22") == "OSA:22:80"


def test_generic_fallback_query_default_is_zero():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "QSA:99") == "OSA:99:0"


def test_iris_commands_are_model_independent():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "#AXI555") == "axi555"
    assert dispatch.handle_command(s, "#GI") == "gi5550"
    assert dispatch.handle_command(s, "#R01") == "s01"


def test_auto_iris_toggle_reflected_in_gi_query():
    s = _state("AW-UE160")
    assert dispatch.handle_command(s, "#GI").endswith("0")
    dispatch.handle_command(s, "ORS:1")
    assert dispatch.handle_command(s, "#GI").endswith("1")


def test_force_er2_once_consumes_itself():
    s = _state("AW-UE160")
    s.force_er2_once = True
    assert dispatch.handle_command(s, "QID") == "ER2:QID"
    assert s.force_er2_once is False
    assert dispatch.handle_command(s, "QID") == "OID:AW-UE160"


def test_set_command_pushes_notification_to_listeners():
    s = _state("AW-UE160")
    pushed = []
    s.push_notification = lambda cmd: pushed.append(cmd)
    dispatch.handle_command(s, "OAF:1")
    assert pushed == ["OAF:1"]


def test_query_command_does_not_push_notification():
    s = _state("AW-UE160")
    pushed = []
    s.push_notification = lambda cmd: pushed.append(cmd)
    dispatch.handle_command(s, "QAF")
    assert pushed == []


def test_iris_commands_are_notification_exempt():
    """Kap. 4.3.1: Iris-Kommandos loesen keine Update-Notification aus."""
    s = _state("AW-UE160")
    pushed = []
    s.push_notification = lambda cmd: pushed.append(cmd)
    dispatch.handle_command(s, "#AXI555")
    assert pushed == []


def test_explicit_exempt_addresses_do_not_push():
    """Kap. 4.3.1 nennt OSE:69/OSD:48/ORV explizit als Ausnahmen."""
    s = _state("AW-UE160")
    pushed = []
    s.push_notification = lambda cmd: pushed.append(cmd)
    dispatch.handle_command(s, "OSD:48:80")
    assert pushed == []

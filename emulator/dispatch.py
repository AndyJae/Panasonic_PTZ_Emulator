"""emulator/dispatch.py -- Kommando-Dispatch fuer den Panasonic-PTZ-Emulator.

Vereint die Doppelpunkt-basierte generische Dispatch-Logik aus
`reference/smart_reset_work_emulator.py` (bleibt Grundlage, siehe TODO.md
Schritt 3) mit der doppelpunktlosen Iris-Behandlung und der
modellabhaengigen Gain-/Pedestal-Simulation aus
`reference/ptz_control_emulator.py`/`reference/ptz_control_panasonic_aw_driver.py`.

Reihenfolge pro Kommando (siehe Plan):
  1. Leer -> ER1:00
  2. ER2-Einmal-Schalter (manueller Test-Hebel)
  3. QID -> OID:<Modell>
  4. #AXI/#GI/#R (Iris, modellunabhaengig)
  5. OGU/QGU (Gain, modellabhaengige Range -> ER3, kein Gain-Katalog -> ER1)
  6. Modell-eigenes PEDESTAL_COMMAND (gleiches Prinzip) + Cross-Modell-Gate
     fuer andere Pedestal-Kommandofamilien
  7. FEATURES-Katalog des aktiven Modells (toggle/trigger/dropdown)
  8. Cross-Modell-Gate: Kommando ist FEATURES-Kommando/-Query eines ANDEREN
     Modells -> ER1 (bildet echte Modellunterschiede ab, z. B. HE50 ohne
     knee_auto)
  9. Generischer Doppelpunkt-Fallback (permissiv, deckt alle nicht
     katalogisierten aber syntaktisch gueltigen Adressen ab -- Reset-
     Sequenzen beider Apps nutzen hunderte solcher Adressen)

Update-Notification-Push: jeder erfolgreich verarbeitete SET-Befehl (nicht
Query) loest automatisch einen Push an alle registrierten Listener aus --
belegt durch Kap. 4 der HDIntegratedCamera-Spec (siehe
reference/ptz_control_CLAUDE.md, "JEDE Kommandoaenderung ... unabhaengig
davon, ob sie von PTZ_Control selbst oder einem anderen Terminal ausgeloest
wurde"). Ausnahmen laut Kap. 4.3.1: OSD-Menue-Navigation, Pan/Tilt/Zoom/
Focus/Iris-Kommandos, OSE:69/OSD:48/ORV.
"""

from __future__ import annotations

from emulator.models import get_registry
from emulator.state import CameraState

_GAIN_ZERO_DB_DATA = 0x08
_GAIN_AGC_DATA = 0x80

# Kap. 4.3.1 der HDIntegratedCamera-Spec: diese Kommandos loesen laut PDF
# keine Update-Notification aus. Iris (#-Kommandos) matcht ueber den
# fuehrenden "#"; die drei explizit genannten Adressen als Praefix-Liste.
_NOTIFICATION_EXEMPT_PREFIXES = ("OSE:69", "OSD:48", "ORV")


def handle_command(state: CameraState, raw_command: str) -> str:
    """Verarbeitet ein einzelnes CGI-Kommando und aktualisiert `state`."""
    command = (raw_command or "").strip().upper()
    if not command:
        return "ER1:00"

    if state.force_er2_once:
        state.force_er2_once = False
        response = f"ER2:{command}"
        state.record(command, response)
        return response

    response, changed = _dispatch(state, command)
    state.record(command, response)
    if changed and not _is_notification_exempt(command):
        state.push_notification(command)
    return response


def _is_notification_exempt(command: str) -> bool:
    if command.startswith("#"):
        return True
    return command.startswith(_NOTIFICATION_EXEMPT_PREFIXES)


def _dispatch(state: CameraState, command: str) -> tuple[str, bool]:
    if command == "QID":
        return f"OID:{state.model_id}", False

    iris_result = _dispatch_iris(state, command)
    if iris_result is not None:
        return iris_result

    gain_result = _dispatch_gain(state, command)
    if gain_result is not None:
        return gain_result

    pedestal_result = _dispatch_pedestal(state, command)
    if pedestal_result is not None:
        return pedestal_result

    features_result = _dispatch_features(state, command)
    if features_result is not None:
        return features_result

    if command in get_registry().all_feature_commands():
        return f"ER1:{command}", False

    return _dispatch_generic(state, command)


def _dispatch_iris(state: CameraState, command: str) -> tuple[str, bool] | None:
    """Doppelpunktlose Iris-Steuerung (`#AXI`/`#GI`/`#R`), aus
    reference/ptz_control_emulator.py::_handle_ptz uebernommen --
    modellunabhaengig, siehe dortiger Docstring."""
    if command.startswith("#AXI") and len(command) == 7:
        try:
            state.iris_data = int(command[4:], 16)
        except ValueError:
            return f"eR1:{command}", False
        return f"axi{command[4:].lower()}", True
    if command == "#GI":
        return f"gi{state.iris_data:03x}{1 if state.auto_iris else 0}", False
    if command.startswith("#R") and len(command) == 4 and command[2:].isdigit():
        return f"s{command[2:]}", True
    return None


def _dispatch_gain(state: CameraState, command: str) -> tuple[str, bool] | None:
    """OGU/QGU (Gain). Encoding (Data = 0x08 + db, 0x80 = AGC) aus
    reference/ptz_control_panasonic_aw_driver.py::_decode_gain_data/
    set_gain_db uebernommen, modelluebergreifend identisch laut beiden
    lokalen Referenz-PDFs -- nur Bereich (GAIN_MIN_DB/GAIN_MAX_DB) ist
    modellabhaengig."""
    if command != "QGU" and not command.startswith("OGU:"):
        return None

    module = state.module
    gain_min = getattr(module, "GAIN_MIN_DB", None) if module else None
    gain_max = getattr(module, "GAIN_MAX_DB", None) if module else None
    if gain_min is None or gain_max is None:
        # Kein Gain-Katalogeintrag fuer dieses Modell -- wie eine echte
        # Kamera ohne dieses Kommando.
        return f"ER1:{command}", False

    if command == "QGU":
        return f"OGU:{state.gain_data:02X}", False

    hex_part = command[len("OGU:"):]
    try:
        data = int(hex_part, 16)
    except ValueError:
        return f"ER1:{command}", False

    if data == _GAIN_AGC_DATA:
        state.gain_data = data
        return command, True

    db = data - _GAIN_ZERO_DB_DATA
    if db < gain_min or db > gain_max:
        return f"ER3:{command}", False

    state.gain_data = data
    return command, True


def _dispatch_pedestal(state: CameraState, command: str) -> tuple[str, bool] | None:
    """Modell-eigenes PEDESTAL_COMMAND/_QUERY_COMMAND (Encoding/Range-Check
    analog zu Gain, siehe reference/ptz_control_panasonic_aw_driver.py::
    set_pedestal/_decode_pedestal_data). Kommandos, die zur Pedestal-Familie
    eines ANDEREN Modells gehoeren, liefern ER1 (Cross-Modell-Gate) --
    Kommandos ausserhalb jeder bekannten Pedestal-Familie fallen durch auf
    den generischen Fallback (koennten unabhaengig davon gueltige Adressen
    im selben Namensraum sein, z. B. OSJ:0D/0E ATW-Ziele)."""
    module = state.module
    ped_cmd = getattr(module, "PEDESTAL_COMMAND", None) if module else None
    ped_query = getattr(module, "PEDESTAL_QUERY_COMMAND", None) if module else None

    if ped_cmd is not None:
        if command == ped_query:
            width = module.PEDESTAL_DATA_WIDTH
            return f"{ped_cmd}:{state.pedestal_data:0{width}X}", False
        set_prefix = f"{ped_cmd}:"
        if command.startswith(set_prefix):
            hex_part = command[len(set_prefix):]
            try:
                data = int(hex_part, 16)
            except ValueError:
                return f"ER1:{command}", False
            scale = module.PEDESTAL_SCALE
            center = module.PEDESTAL_CENTER_DATA
            value = (data - center) // scale
            if value < module.PEDESTAL_MIN or value > module.PEDESTAL_MAX:
                return f"ER3:{command}", False
            state.pedestal_data = data
            return command, True

    for family_cmd, family_query in get_registry().all_pedestal_families():
        if family_cmd == ped_cmd:
            continue  # eigene Familie, oben bereits behandelt
        if command == family_query or command.startswith(f"{family_cmd}:"):
            return f"ER1:{command}", False

    return None


def _dispatch_features(state: CameraState, command: str) -> tuple[str, bool] | None:
    """FEATURES-Katalog des aktiven Modells (toggle/trigger/dropdown, siehe
    emulator/models/aw_ue160.py fuer die Struktur)."""
    module = state.module
    if module is None:
        return None

    for feature in getattr(module, "FEATURES", {}).values():
        kind = feature.get("kind")
        query_cmd = feature.get("query")

        if kind == "toggle":
            on = feature.get("on")
            off = feature.get("off")
            on_list = [on] if isinstance(on, str) else list(on or [])
            off_list = [off] if isinstance(off, str) else list(off or [])
            if command in on_list or command in off_list:
                if query_cmd:
                    is_on = command in on_list
                    state.feature_values[query_cmd] = feature.get("query_on_value", "1") if is_on else "0"
                if command in ("ORS:1", "ORS:0"):
                    state.auto_iris = command == "ORS:1"
                return command, True
            if query_cmd and command == query_cmd:
                value = state.feature_values.get(query_cmd, "0")
                return f"O{query_cmd[1:]}:{value}", False

        elif kind == "trigger":
            if command == feature.get("cmd"):
                return command, True

        elif kind == "dropdown":
            for _label, option_cmd in feature.get("options", []):
                if command == option_cmd:
                    if query_cmd:
                        state.feature_values[query_cmd] = option_cmd.rsplit(":", 1)[-1]
                    return command, True
            if query_cmd and command == query_cmd:
                value = state.feature_values.get(query_cmd, "0")
                return f"O{query_cmd[1:]}:{value}", False

    return None


def _dispatch_generic(state: CameraState, command: str) -> tuple[str, bool]:
    """Generischer Doppelpunkt-Dispatch aus
    reference/smart_reset_work_emulator.py::_handle_command -- jedes
    syntaktisch gueltige `<Praefix><Rest>:<Wert>` wird gespeichert und
    echot, `Q<Rest>` liefert den zuletzt gespeicherten Wert (Default "0").
    Bleibt bewusst permissiv, siehe Modul-Docstring."""
    if command.startswith("Q"):
        key = command[1:]
        value = state.generic_values.get(key, "0")
        prefix = state.generic_prefixes.get(key, "O")
        return f"{prefix}{key}:{value}", False

    prefix = command[0]
    body = command[1:]
    parts = body.split(":")
    if len(parts) >= 2:
        key = ":".join(parts[:-1])
        state.generic_values[key] = parts[-1]
        state.generic_prefixes[key] = prefix
        return command, True

    return command, False

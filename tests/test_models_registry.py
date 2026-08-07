"""Tests fuer emulator/models/__init__.py -- Registry-Aufloesung, Aliase."""

from emulator.models import get_registry


def test_all_17_models_load_without_error():
    ids = get_registry().registered_camera_ids()
    assert len(ids) == 17


def test_he145_resolves_and_ue145_is_alias():
    registry = get_registry()
    module = registry.resolve("AW-HE145")
    assert module is not None
    assert module.CAMERA_ID == "AW-HE145"
    assert registry.resolve("AW-UE145") is module


def test_he42_resolves_and_shares_he40_catalog():
    registry = get_registry()
    he42 = registry.resolve("AW-HE42")
    he40 = registry.resolve("AW-HE40")
    assert he42 is not None
    assert registry.resolve("AW-HE75") is he42  # Alias
    assert he42.FEATURES is he40.FEATURES
    assert he42.GAIN_MIN_DB == he40.GAIN_MIN_DB


def test_ue150a_aliases():
    registry = get_registry()
    module = registry.resolve("AW-UE150A")
    for alias in ("AW-UE150", "AW-UE155", "AW-UN145"):
        assert registry.resolve(alias) is module


def test_unknown_model_resolves_to_none():
    assert get_registry().resolve("AW-DOES-NOT-EXIST") is None
    assert get_registry().resolve(None) is None


def test_ak_ub300_has_no_gain_but_has_pedestal():
    module = get_registry().resolve("AK-UB300")
    assert getattr(module, "GAIN_MIN_DB", None) is None
    assert module.PEDESTAL_COMMAND == "OSG:4A"


def test_three_distinct_pedestal_families():
    families = {cmd for cmd, _query in get_registry().all_pedestal_families()}
    assert families == {"OSJ:0F", "OTP", "OSG:4A"}


def test_all_feature_commands_nonempty_and_includes_known_entries():
    commands = get_registry().all_feature_commands()
    assert "OAF:1" in commands  # auto_focus on, geteilt von fast allen Modellen
    assert "OSA:2D:2" in commands  # knee_auto (HE130 u.a.)
    assert len(commands) > 50

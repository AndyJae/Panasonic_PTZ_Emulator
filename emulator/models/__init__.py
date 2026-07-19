"""emulator.models -- Modell-Registry fuer den Panasonic-PTZ-Emulator.

Laedt beim ersten Zugriff alle Modell-Module aus diesem Paket und indiziert
sie nach CAMERA_ID (+ optionalen CAMERA_ID_ALIASES). Angelehnt an
reference/ptz_control_panasonic_models/registry.py, aber ohne
Laufzeit-Abhaengigkeit zu einer der beiden Referenz-Apps.

Jedes Modell-Modul definiert:
    CAMERA_ID: str
    CAMERA_ID_ALIASES: list[str]           (optional)
    DISPLAY_NAME: str
    GAIN_MIN_DB / GAIN_MAX_DB / GAIN_STEP_DB: int   (optional, fehlt z.B. bei AK-UB300)
    PEDESTAL_COMMAND / PEDESTAL_QUERY_COMMAND: str  (optional)
    PEDESTAL_MIN / PEDESTAL_MAX / PEDESTAL_CENTER_DATA / PEDESTAL_SCALE / PEDESTAL_DATA_WIDTH: int
    FEATURES: dict[str, dict]              -- kind: "toggle" | "trigger" | "dropdown"
    FEATURE_LABELS: dict[str, str]
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

_PACKAGE_NAME = __name__


def feature_commands(module: ModuleType) -> set[str]:
    """Alle literalen Kommando-Strings aus module.FEATURES (on/off/cmd/
    Dropdown-Options sowie die zugehoerigen query-Kommandos) -- Grundlage
    fuer das Cross-Modell-Gate in dispatch.py. query-Kommandos sind
    enthalten, damit z.B. "QSA:2D" (Knee-Query) auf einem Modell ohne
    Knee-Feature korrekt ER1 statt eines erfundenen generischen
    Default-Werts liefert."""
    commands: set[str] = set()
    for feature in getattr(module, "FEATURES", {}).values():
        kind = feature.get("kind")
        query = feature.get("query")
        if query:
            commands.add(query)
        if kind == "toggle":
            for side in (feature.get("on"), feature.get("off")):
                if side is None:
                    continue
                if isinstance(side, str):
                    commands.add(side)
                else:
                    commands.update(side)
        elif kind == "trigger":
            cmd = feature.get("cmd")
            if cmd:
                commands.add(cmd)
        elif kind == "dropdown":
            for _label, cmd in feature.get("options", []):
                if cmd:
                    commands.add(cmd)
    return commands


class ModelRegistry:
    def __init__(self) -> None:
        self._models: dict[str, ModuleType] = {}
        self._by_module_name: dict[str, ModuleType] = {}
        self._all_feature_commands: set[str] | None = None
        self._all_pedestal_families: set[tuple[str, str]] | None = None

    def register(self, module: ModuleType) -> None:
        camera_id = getattr(module, "CAMERA_ID", "")
        if not camera_id or not isinstance(camera_id, str):
            return
        self._models[camera_id] = module
        for alias in getattr(module, "CAMERA_ID_ALIASES", []):
            if isinstance(alias, str) and alias.strip():
                self._models[alias.strip()] = module
        self._by_module_name[module.__name__.rsplit(".", 1)[-1]] = module
        self._all_feature_commands = None  # invalidate cache
        self._all_pedestal_families = None

    def resolve(self, camera_id: str | None) -> ModuleType | None:
        if not camera_id:
            return None
        return self._models.get(camera_id)

    def registered_camera_ids(self) -> list[str]:
        return sorted(
            {getattr(m, "CAMERA_ID", "") for m in self._by_module_name.values() if getattr(m, "CAMERA_ID", "")}
        )

    def all_modules(self) -> list[ModuleType]:
        return list(self._by_module_name.values())

    def all_feature_commands(self) -> set[str]:
        """Vereinigungsmenge aller FEATURES-Kommandos ueber alle Modelle --
        einmalig gebaut, dann gecacht (siehe register() fuer Invalidierung)."""
        if self._all_feature_commands is None:
            commands: set[str] = set()
            for module in self._by_module_name.values():
                commands |= feature_commands(module)
            self._all_feature_commands = commands
        return self._all_feature_commands

    def all_pedestal_families(self) -> set[tuple[str, str]]:
        """Vereinigungsmenge aller (PEDESTAL_COMMAND, PEDESTAL_QUERY_COMMAND)-
        Paare ueber alle Modelle -- Grundlage fuer das Cross-Modell-Gate bei
        Pedestal-Kommandos einer anderen Kommandofamilie als der des aktiven
        Modells (siehe dispatch.py)."""
        if self._all_pedestal_families is None:
            families: set[tuple[str, str]] = set()
            for module in self._by_module_name.values():
                cmd = getattr(module, "PEDESTAL_COMMAND", None)
                query = getattr(module, "PEDESTAL_QUERY_COMMAND", None)
                if cmd and query:
                    families.add((cmd, query))
            self._all_pedestal_families = families
        return self._all_pedestal_families

    def load_package(self, package_name: str = _PACKAGE_NAME) -> int:
        package = importlib.import_module(package_name)
        loaded = 0
        for info in pkgutil.iter_modules(package.__path__):
            full_name = f"{package_name}.{info.name}"
            module = importlib.import_module(full_name)
            self.register(module)
            loaded += 1
        return loaded


_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    """Lazy Singleton -- einmalig befuellt, danach nur gelesen."""
    global _registry
    if _registry is None:
        _registry = ModelRegistry()
        _registry.load_package()
    return _registry


def resolve_model(camera_id: str | None) -> ModuleType | None:
    return get_registry().resolve(camera_id)

"""emulator/tray.py -- System-Tray-Icon fuer den laufenden Emulator-Prozess.

Zeigt images/Icon.ico im System-Tray, solange der Prozess laeuft. Linksklick
auf das Icon (bzw. Menuepunkt "Open") oeffnet die Control-UI im Browser,
Menuepunkt "Quit" stoppt den Prozess.
"""

from __future__ import annotations

import webbrowser
from pathlib import Path
from typing import Callable

import pystray
from PIL import Image

ICON_PATH = Path(__file__).resolve().parent.parent / "images" / "Icon.ico"


def run(title: str, url: str, on_quit: Callable[[], None]) -> None:
    """Blockiert im aufrufenden Thread, bis ueber das Tray-Menue beendet wird."""
    image = Image.open(ICON_PATH)

    def Open(icon: pystray.Icon, item: pystray.MenuItem) -> None:
        webbrowser.open(url)

    def Quit(icon: pystray.Icon, item: pystray.MenuItem) -> None:
        icon.stop()
        on_quit()

    menu = pystray.Menu(
        pystray.MenuItem("Open", Open, default=True),
        pystray.MenuItem("Quit", Quit),
    )
    icon = pystray.Icon("panasonic_ptz_emulator", image, title, menu)
    icon.run()

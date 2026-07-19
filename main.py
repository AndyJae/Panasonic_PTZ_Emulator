"""main.py -- Einstiegspunkt fuer den Panasonic-PTZ-Emulator.

Start:
    python main.py [--ui-port 8080] [--port 8081] [--model AW-UE160]

Aequivalent zu `python -m emulator`, siehe emulator/__main__.py.
"""

from emulator.server import main

if __name__ == "__main__":
    main()

# Panasonic PTZ Emulator

A standalone Panasonic PTZ camera CGI emulator — it pretends to be a real
Panasonic AW/AK-series camera on the network, so you can develop and test
against it without needing physical hardware.

This tool was built explicitly to serve two other projects that both talk to
real Panasonic cameras over the same CGI protocol:

- **[smart-reset-browser](https://github.com/AndyJae/smart-reset-browser)** —
  browser-based PTZ camera reset/control/NDI monitoring tool.
- **[X-Touch_PTZ_Control](https://github.com/AndyJae/X-Touch_PTZ_Control)** —
  MIDI shading/iris controller for the Behringer X-Touch Extender.

Neither app depends on this repo at runtime, and this repo doesn't depend on
either of them — it's a separate process you point your app at instead of a
real camera's IP address.

Contributions are welcome — new camera models, protocol fixes, additional
simulated commands, or support for other Panasonic-CGI-based apps beyond the
two above.

## What it simulates

- Both command dialects used by real Panasonic cameras: colon-based
  (`O<cmd>:<addr>:<value>` / `Q<cmd>:<addr>`) and colon-less `#`-prefixed
  commands (`#AXI`, `#GI`, `#R`) used for iris/preset control.
- Per-model gain and pedestal simulation (range, step size, command family —
  these differ across models).
- `ER1`/`ER2`/`ER3` error responses (syntax error, busy, out-of-range),
  including a manual "next command returns ER2 (busy)" toggle for testing
  error handling.
- The camera's update-notification push channel (`/cgi-bin/event`) — any
  successful set command automatically pushes a notification frame to every
  registered listener, just like a real camera reports changes made from its
  own web UI or another controller.
- 16 camera models (see `emulator/models/`): AW-UE160, AW-UE150A (+ AW-UE150 alias), AW-UE100,
  AW-UE80, AW-UE70, AW-UE50, AW-UE40, AW-UE30, AW-HE145 (+ AW-UE145 alias), AW-HE130, AW-HE120,
  AW-HE60, AW-HE50, AW-HE42, AW-HE40, AW-HR140.

## Running it

```
python main.py [--host 127.0.0.1] [--ui-port 8080] [--port 8081] [--model AW-UE160]
```

This starts a control UI at `http://127.0.0.1:8080/` where you pick a camera
model and port and start/stop the simulated camera's CGI server (default
port `8081`) — it only listens while "started", so a connection attempt
while stopped behaves like a powered-off camera (connection refused). The
control UI also shows live camera state (iris/gain/pedestal/ND/bars), a log
of the last commands, a field to inject a command as if it came from the
camera's own web UI, and the ER2 toggle mentioned above.

Point your app at `127.0.0.1:8081` (or whatever `--port` you chose) instead
of a real camera's IP.

## Development

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\pytest
```

Core pieces:
- `emulator/dispatch.py` — command dispatch (both protocol dialects, gain/
  pedestal range checks, per-model feature catalog, generic fallback).
- `emulator/models/*.py` — one file per camera model (gain/pedestal
  ranges, button features, ND filter options).
- `emulator/state.py` — simulated per-instance camera state.
- `emulator/notify.py` — update-notification frame encoding/decoding.
- `emulator/server.py` — the two FastAPI apps (control UI + camera CGI
  server) and `main()` entry point.

## License

Apache License 2.0 — see [LICENSE](LICENSE).

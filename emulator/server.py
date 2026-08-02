"""emulator/server.py -- Panasonic PTZ CGI-Kamera-Emulator: Control-UI +
CGI-Server in einem Prozess.

Zwei Server, wie in beiden Referenzquellen:
  - Control-UI (immer erreichbar auf --ui-port): Modell/Port waehlen,
    Start/Stop, Log/Zustand ansehen, externe Aenderung simulieren,
    naechsten Befehl auf ER2 (busy) setzen.
  - Kamera-CGI-Server (--port): hoert nur, waehrend "gestartet". Stop gibt
    den Port tatsaechlich frei, ein Connect-Versuch waehrend "gestoppt"
    bekommt ein echtes Connection-Refused, wie bei einer ausgeschalteten
    Kamera (siehe reference/smart_reset_work_emulator.py).
"""

from __future__ import annotations

import threading
import time
import webbrowser
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Form, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse, Response

from emulator import dispatch
from emulator.discovery import create_discovery_socket, discovery_responder_loop
from emulator.models import get_registry
from emulator.state import CameraState

ICON_PATH = Path(__file__).resolve().parent.parent / "images" / "Icon.ico"

MODEL_IDS = get_registry().registered_camera_ids()
if not MODEL_IDS:
    raise SystemExit("Keine Kameramodelle unter emulator/models/ gefunden.")

state = CameraState(MODEL_IDS[0])

# ---------------------------------------------------------------------------
# Kamera-CGI-Server -- hoert nur, waehrend "gestartet"
# ---------------------------------------------------------------------------

cgi_app = FastAPI()


@cgi_app.get("/cgi-bin/aw_cam")
async def aw_cam(cmd: str = "") -> PlainTextResponse:
    return PlainTextResponse(dispatch.handle_command(state, cmd))


@cgi_app.get("/cgi-bin/aw_ptz")
async def aw_ptz(cmd: str = "") -> PlainTextResponse:
    return PlainTextResponse(dispatch.handle_command(state, cmd))


@cgi_app.get("/cgi-bin/event")
async def cgi_event(request: Request, connect: str = "", my_port: int = 0, uid: int = 0) -> Response:
    """Update-Notification-Registrierung (siehe Interface-Specs, "Camera
    information update notification"): connect=start registriert my_port
    fuer jeden kuenftigen Set-Befehl (siehe dispatch.py), connect=stop
    deregistriert. Beides mit 204 No Content beantwortet, laut Spec."""
    host = request.client.host if request.client else "127.0.0.1"
    if connect == "start" and my_port:
        state.listeners[my_port] = host
        state.record(f"event?connect=start&my_port={my_port}", "204")
    elif connect == "stop" and my_port:
        state.listeners.pop(my_port, None)
        state.record(f"event?connect=stop&my_port={my_port}", "204")
    return Response(status_code=204)


class ServerManager:
    """Startet/stoppt den Kamera-CGI-Server (uvicorn) und den UDP-Discovery-
    Responder (siehe discovery.py) zusammen, in Hintergrund-Threads."""

    def __init__(self) -> None:
        self.server: uvicorn.Server | None = None
        self.thread: threading.Thread | None = None
        self.host: str = "127.0.0.1"
        self.port: int | None = None
        self.error: str | None = None
        self.discovery_thread: threading.Thread | None = None
        self.discovery_stop_event: threading.Event | None = None
        self.discovery_error: str | None = None

    @property
    def running(self) -> bool:
        return self.thread is not None and self.thread.is_alive()

    def start(self, host: str, port: int, model_id: str) -> None:
        if self.running:
            return
        self.error = None
        state.reset(model_id)

        config = uvicorn.Config(cgi_app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        self.server = server
        self.host = host
        self.port = port
        thread.start()
        self.thread = thread

        for _ in range(60):
            if server.started or not thread.is_alive():
                break
            time.sleep(0.05)

        if not server.started:
            self.error = f"Port {port} konnte nicht gebunden werden (belegt?)."
            self.thread = None
            self.server = None
            self.port = None
            return

        # UDP-Discovery-Responder -- gleicher Lifecycle wie der CGI-Server,
        # damit der Emulator nur waehrend des tatsaechlichen Laufens per
        # "Scan Network" auffindbar ist. Bind-Fehlschlag ist nicht fatal
        # (die Kamera laeuft trotzdem, nur eben nicht per Scan auffindbar) --
        # aber sichtbar machen statt still zu scheitern (z. B. weil noch ein
        # anderer Prozess Port 10670 haelt).
        discovery_sock = create_discovery_socket()
        if discovery_sock is None:
            self.discovery_error = (
                "UDP-Discovery-Port 10670 konnte nicht gebunden werden (belegt?) -- "
                "Kamera laeuft, ist aber per \"Scan Network\" nicht auffindbar."
            )
        else:
            self.discovery_error = None
            stop_event = threading.Event()
            discovery_thread = threading.Thread(
                target=discovery_responder_loop,
                args=(discovery_sock, stop_event, host, port, model_id),
                daemon=True,
            )
            self.discovery_stop_event = stop_event
            discovery_thread.start()
            self.discovery_thread = discovery_thread

    def stop(self) -> None:
        if self.server:
            self.server.should_exit = True
        if self.thread:
            self.thread.join(timeout=5)
        self.server = None
        self.thread = None
        self.port = None

        if self.discovery_stop_event:
            self.discovery_stop_event.set()
        if self.discovery_thread:
            self.discovery_thread.join(timeout=2)
        self.discovery_thread = None
        self.discovery_stop_event = None


manager = ServerManager()


# ---------------------------------------------------------------------------
# Control-UI -- immer erreichbar
# ---------------------------------------------------------------------------

control_app = FastAPI()

_PAGE = """<!doctype html>
<html><head><title>Panasonic PTZ Emulator</title>
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<style>
body {{ font-family: sans-serif; max-width: 760px; margin: 2rem auto; padding: 0 1rem; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }}
td, th {{ border: 1px solid #ccc; padding: 4px 8px; text-align: left; font-size: 0.85em; }}
form {{ margin: 1rem 0; }}
label {{ display: block; margin: 0.5rem 0; }}
select {{ font-size: 1em; }}
.error {{ color: #b00020; }}
.warn {{ color: #b06000; }}
</style></head>
<body>
<h1>Panasonic PTZ Emulator</h1>
{status_block}
{log_state_block}
{script}
</body></html>"""

_STOPPED_BLOCK = """<form method="post" action="/start">
<label>Kamera-Modell:
<select name="model_id">{options}</select>
</label>
<label>Port:
<input type="number" name="port" value="{port}" min="1" max="65535">
</label>
<button type="submit">Server starten</button>
</form>
{error}
<p>Status: <b>gestoppt</b> &mdash; unter dieser Adresse ist aktuell keine Kamera erreichbar.</p>"""

_RUNNING_BLOCK = """<p>Status: <b>l&auml;uft</b> &mdash; Modell <b>{model_id}</b> auf <code>{host}:{port}</code></p>
<p>&Uuml;ber "Scan Network" auffindbar (UDP-Discovery-Antwort aktiv, Port 10670). Das eigentliche &Auml;ndern von IP/DHCP wird vom Emulator nicht beantwortet.</p>
{discovery_error}
<form method="post" action="/stop"><button type="submit">Server stoppen</button></form>
<h2>Update-Notification-Listener</h2>
<p id="listeners-value">{listeners}</p>
<form method="post" action="/simulate-change">
<label>Befehl als externe &Auml;nderung simulieren (z.&nbsp;B. &uuml;ber die Kamera-Web-UI ge&auml;ndert):
<input type="text" name="command" placeholder="OSA:0D:1" style="width: 220px;">
</label>
<button type="submit">Senden</button>
</form>
<form method="post" action="/force-er2">
<button type="submit">N&auml;chster Befehl liefert ER2 (busy){er2_marker}</button>
</form>"""

_LOG_STATE_BLOCK = """<h2>Kamera-Zustand</h2>
<table>
<tr><td>Iris (hex)</td><td id="iris-value">{iris}</td></tr>
<tr><td>Auto-Iris</td><td id="auto-iris-value">{auto_iris}</td></tr>
<tr><td>Gain (hex)</td><td id="gain-value">{gain}</td></tr>
<tr><td>Pedestal (hex)</td><td id="pedestal-value">{pedestal}</td></tr>
<tr><td>ND-Index</td><td id="nd-value">{nd}</td></tr>
<tr><td>Bars</td><td id="bars-value">{bars}</td></tr>
</table>
<h2>Letzte Befehle</h2>
<table><thead><tr><th>#</th><th>Befehl -&gt; Antwort</th></tr></thead><tbody id="log-rows">{log_rows}</tbody></table>
<p><a href="/">Aktualisieren</a> (aktualisiert sich auch automatisch)</p>"""

_SCRIPT = """<script>
async function pollState() {
  const logRows = document.getElementById("log-rows");
  if (!logRows) return;

  let data;
  try {
    const res = await fetch("/state.json");
    if (!res.ok) return;
    data = await res.json();
  } catch (err) {
    return;
  }
  if (!data.running) return;

  const setText = (id, value) => {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  };
  setText("iris-value", data.iris);
  setText("auto-iris-value", data.auto_iris);
  setText("gain-value", data.gain);
  setText("pedestal-value", data.pedestal);
  setText("nd-value", data.nd);
  setText("bars-value", data.bars);
  setText("listeners-value", data.listeners);

  logRows.innerHTML = "";
  if (data.log.length === 0) {
    const row = document.createElement("tr");
    row.innerHTML = "<td colspan='2'>&mdash;</td>";
    logRows.appendChild(row);
  } else {
    data.log.forEach((entry, i) => {
      const row = document.createElement("tr");
      const numCell = document.createElement("td");
      numCell.textContent = String(i + 1);
      const entryCell = document.createElement("td");
      entryCell.textContent = entry;
      row.appendChild(numCell);
      row.appendChild(entryCell);
      logRows.appendChild(row);
    });
  }
}
setInterval(pollState, 1000);
</script>"""


def _state_snapshot() -> dict:
    """Aktueller Kamerazustand fuer UI-Rendering und `/state.json` (Grundlage
    fuer den JS-Live-Poll, siehe _SCRIPT) -- eine gemeinsame Quelle, damit
    beide Darstellungen nicht auseinanderlaufen."""
    module = state.module
    gain_text = (
        f"{state.gain_data:02X}"
        if module is not None and getattr(module, "GAIN_MIN_DB", None) is not None
        else "n/a (Modell hat kein OGU)"
    )
    pedestal_text = (
        f"{state.pedestal_data:0{module.PEDESTAL_DATA_WIDTH}X}"
        if module is not None and getattr(module, "PEDESTAL_COMMAND", None) is not None
        else "n/a (Modell hat kein Pedestal-Kommando)"
    )
    listeners_text = (
        ", ".join(f"{host}:{port}" for port, host in state.listeners.items())
        or "keine registriert"
    )
    return {
        "model_id": state.model_id,
        "iris": f"{state.iris_data:03X}",
        "auto_iris": state.auto_iris,
        "gain": gain_text,
        "pedestal": pedestal_text,
        "nd": state.nd_index,
        "bars": state.bars_on,
        "listeners": listeners_text,
        "log": list(reversed(state.log)),
    }


def _render() -> str:
    if manager.running:
        snap = _state_snapshot()
        er2_marker = " (aktiv)" if state.force_er2_once else ""
        discovery_error = (
            f'<p class="warn">{manager.discovery_error}</p>' if manager.discovery_error else ""
        )
        status_block = _RUNNING_BLOCK.format(
            model_id=snap["model_id"], host=manager.host, port=manager.port,
            listeners=snap["listeners"], er2_marker=er2_marker,
            discovery_error=discovery_error,
        )

        log_rows = "".join(
            f"<tr><td>{i + 1}</td><td>{entry}</td></tr>"
            for i, entry in enumerate(snap["log"])
        ) or "<tr><td colspan='2'>&mdash;</td></tr>"
        log_state_block = _LOG_STATE_BLOCK.format(
            iris=snap["iris"], auto_iris=snap["auto_iris"],
            gain=snap["gain"], pedestal=snap["pedestal"],
            nd=snap["nd"], bars=snap["bars"],
            log_rows=log_rows,
        )
        script = _SCRIPT
    else:
        options = "".join(
            f'<option value="{mid}"{" selected" if mid == state.model_id else ""}>{mid}</option>'
            for mid in MODEL_IDS
        )
        error = f'<p class="error">{manager.error}</p>' if manager.error else ""
        status_block = _STOPPED_BLOCK.format(
            options=options, port=manager.port or 8081, error=error
        )
        log_state_block = ""
        script = ""

    return _PAGE.format(status_block=status_block, log_state_block=log_state_block, script=script)


@control_app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> FileResponse:
    return FileResponse(ICON_PATH)


@control_app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _render()


@control_app.get("/state.json")
async def state_json() -> dict:
    """Wird von _SCRIPT gepollt, um Zustand/Log ohne vollen Seiten-Reload zu
    aktualisieren."""
    if not manager.running:
        return {"running": False}
    return {"running": True, **_state_snapshot()}


@control_app.post("/start")
async def start(model_id: str = Form(...), port: int = Form(...)) -> RedirectResponse:
    if model_id in MODEL_IDS:
        manager.start(manager.host, port, model_id)
    return RedirectResponse("/", status_code=303)


@control_app.post("/stop")
async def stop() -> RedirectResponse:
    manager.stop()
    return RedirectResponse("/", status_code=303)


@control_app.post("/simulate-change")
async def simulate_change(command: str = Form(...)) -> RedirectResponse:
    """Stellvertretend fuer "jemand hat eine Einstellung ueber die
    Kamera-eigene Web-UI geaendert": laeuft ueber denselben Dispatch-Pfad
    wie ein echter Client-Befehl (inkl. automatischem Notification-Push,
    siehe dispatch.py) -- kein separater Code-Pfad mehr wie im
    smart_reset_work-Vorbild."""
    command = command.strip()
    if command and manager.running:
        dispatch.handle_command(state, command)
    return RedirectResponse("/", status_code=303)


@control_app.post("/force-er2")
async def force_er2() -> RedirectResponse:
    """Manueller Einmal-Schalter: der naechste eingehende Befehl liefert
    ER2 (busy) statt der normalen Antwort. Kein PDF-Beleg fuer eine
    automatische Ausloesebedingung (siehe Plan) -- bewusst nur als
    explizites Test-Werkzeug fuer die beiden Consumer-Apps."""
    if manager.running:
        state.force_er2_once = True
    return RedirectResponse("/", status_code=303)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Panasonic PTZ CGI-Kamera-Emulator")
    parser.add_argument("--host", default="127.0.0.1", help="Bind-Adresse fuer UI und Kamera-Server")
    parser.add_argument("--ui-port", type=int, default=8080, help="Port der Steuer-UI")
    parser.add_argument("--port", type=int, default=8081, help="Vorbelegter Kamera-Port im Start-Formular")
    parser.add_argument("--model", default=None, help="Vorausgewaehltes Kameramodell", choices=MODEL_IDS)
    args = parser.parse_args()

    manager.host = args.host
    manager.port = args.port
    if args.model:
        state.model_id = args.model

    print(f"Panasonic PTZ Emulator UI: http://{args.host}:{args.ui_port}/")
    print(f"Verfuegbare Modelle: {', '.join(MODEL_IDS)}")

    ui_config = uvicorn.Config(control_app, host=args.host, port=args.ui_port, log_level="warning")
    ui_server = uvicorn.Server(ui_config)
    ui_thread = threading.Thread(target=ui_server.run, daemon=True)
    ui_thread.start()

    def _open_browser() -> None:
        """Wait briefly for the server to be ready, then open the browser."""
        time.sleep(1.2)
        webbrowser.open(f"http://{args.host}:{args.ui_port}/")

    threading.Thread(target=_open_browser, daemon=True).start()

    def _shutdown() -> None:
        manager.stop()
        ui_server.should_exit = True
        ui_thread.join(timeout=5)

    from emulator import tray

    ui_url = f"http://{args.host}:{args.ui_port}/"
    tray.run(f"Panasonic PTZ Emulator ({args.host}:{args.ui_port})", ui_url, _shutdown)


if __name__ == "__main__":
    main()

# CHANGELOG — Panasonic_PTZ_Emulator

Feature-by-feature engineering log: what was found, fixed, and verified — merge progress,
cross-repo verification, and one-time repo-history changes. For current architecture and
behavioral guidelines, see `CLAUDE.md`.

---

## Merge progress (2026-07-27)

The merge is by now largely implemented, not just planned — `emulator/` contains a standalone
dispatch (`dispatch.py`), 17 model catalogs (16 selectable in the dropdown, AK-UB300 registered
but deliberately hidden — see the 2026-08-07 entry below) (`emulator/models/*.py`), state
management (`state.py`), update-notification encoding/push (`notify.py`), and a control UI + CGI
server (`server.py`, entry point `main.py`, tray icon `tray.py`) — TODO.md steps 1–5 and 7 are
done per commit history (`0a161f9 Implement merged Panasonic PTZ CGI emulator (TODO.md steps
1-5, 7)`, then `186a58c`/`9632171` for entry point/tray icon), including the ER2/ER3 simulation
TODO.md step 4 still listed as missing and automatic notification push on every set-change (not
just via the manual "simulate" button). Own test suite: 43/43 tests green (`pytest`, as of
2026-07-27). Additionally live-verified against the real `PanasonicAWDriver` from `PTZ_Control`
(real HTTP round trip, no mock): iris set/read, gain incl. ER3 range errors and Auto/AGC state,
pedestal, button feature toggle (`auto_focus`), and update-notification push all arrived
correctly at the driver.

## UDP discovery response added (2026-08-02)

New module `emulator/discovery.py` (`build_discovery_response`, `discovery_responder_loop`) — the
emulator now answers UDP discovery requests (port 10670 → response goes directly to the sender,
no fixed response-port binding needed), so `smart_reset_work`'s "Scan Network" finds it.
`ServerManager` in `server.py` starts/stops the responder thread together with the CGI server.
**1:1 port from `smart_reset_work/smart_reset/discovery.py`**, where the byte format was
verified in a separate session against the official interface-spec PDFs as well as independently
against a public reference implementation (see `discovery.py`'s docstring here) — since
`docs/specs/` was removed from this repo (see "Reference material removed" below), no new PDF
check was done here, only the already-verified contract was carried over.

Covers only the *read* side (discovery). The *write* side (set IP / DHCP reset via the JSON+TLV
handshake on port 10671/10672 + 10669/10670) is **not** implemented — a "Set IP" attempt from
`smart_reset_work` against this emulator goes unanswered (a clean failure, not a crash).
Deliberate scope boundary of this change, not a gap.

Tested: 6 new tests (`tests/test_discovery.py` — packet construction in isolation;
`tests/test_emulator_http.py::test_udp_discovery_responds_to_real_request_and_stops_with_server`
— a real UDP round trip with a byte-identical reconstruction of a real discovery request against
a server actually started via `ServerManager`, plus verification that nothing answers anymore
after `/stop`). Full suite: 49/49 green (`pytest`, as of 2026-08-02).

## Cross-repo live verification (2026-08-02)

`smart_reset_work`'s own, unmodified `smart_reset/discovery.py::discover_cameras()` client found
this emulator (started via `ServerManager.start()`) via a real UDP broadcast and parsed it
correctly — model, IP, port, MAC, netmask, gateway all arrived correctly. No mock, two real
processes over real sockets (the test ran in the same Python process, but with real OS sockets,
not in-memory). Directly reproduced what `smart_reset_work`'s own CLAUDE.md had noted as an open
gap at the time.

**Found and fixed along the way:** a first test run failed because a process from a previous test
run still held port 10670 — the discovery bind failure stayed completely invisible (the camera
ran fine, `discovery_error` didn't exist yet, no indication anywhere). Fixed by splitting
`create_discovery_socket()`/`discovery_responder_loop()` apart (mirroring `smart_reset_work`'s own
`create_discovery_socket()`/`discover_cameras()` split) and adding `ServerManager.discovery_error`,
shown as a warning in the control UI as soon as the bind fails — previously a purely silent
failure mode.

**Still open (TODO.md step 6, not part of this repo):** neither `smart_reset_work` nor
`PTZ_Control` has switched to this tool yet — both still use their own `tools/panasonic_emulator.py`
copy. No live test against `smart_reset_work` was done (its consumer code doesn't point at any
external emulator yet). The cross-model gate (a command belonging to a different model → `ER1`)
was not separately live-verified, only present in code.

*(Resolved 2026-08-07: `smart_reset_work`'s own reset sequences have since been live-verified
end-to-end against this emulator for every comparable model — see the 2026-08-07 entries below.
`smart_reset_work` still uses its own `tools/panasonic_emulator.py` for day-to-day work, though;
switching over is still open.)*

## Reference material removed for publication (2026-07-27)

**Removed (user request 2026-07-27, preparing for a public repo):** `reference/` and
`docs/specs/` contained a real internal camera IP (`192.168.0.10`, from the copied
`smart_reset_work_CLAUDE.md`) and seven official, copyrighted Panasonic/Behringer interface-spec
PDFs — neither suitable for a public repo. Since both folders were already present in the very
first commit (`Scaffold ...`), a plain `git rm` wasn't enough (the files would have stayed
retrievable via commit history) — the entire history was rewritten with `git filter-repo --path
reference --invert-paths --path docs --invert-paths` and force-pushed, then `.gitignore` was
extended with `reference/`/`docs/`. Both folders still exist locally (not part of the repo) under
`C:\GitHub\Panasonic_PTZ_Emulator_reference_backup` for continued work on this machine.

Original contents (now only in the local backup, no longer in the repo):

| File/folder | Origin | Content |
|---|---|---|
| `reference/smart_reset_work_emulator.py` | `smart_reset_work/tools/panasonic_emulator.py` | Generic dispatch, update-notification push |
| `reference/ptz_control_emulator.py` | `PTZ_Control/tools/panasonic_emulator.py` | Explicit per-command handling, gain/pedestal, `#` commands |
| `reference/ptz_control_panasonic_aw_driver.py` | `PTZ_Control/drivers/panasonic_aw.py` | Real driver incl. notification parsing (`_handle_notification`) — reference for gain/pedestal decoding |
| `reference/smart_reset_work_camera_plugins/` | `smart_reset_work/camera_plugins/panasonic/` | `UI_BUTTONS`/`UI_DROPDOWNS`/`RESET_COMMANDS`/`UI_FEATURE_QUERIES` per model (19 files incl. `notify.py`, `transport.py`, `base.py`) |
| `reference/ptz_control_panasonic_models/` | `PTZ_Control/drivers/panasonic_models/` | `BUTTON_FEATURES` + gain/pedestal constants per model (independently verified against PDFs, sometimes differing from smart_reset_work) |
| `reference/smart_reset_work_CLAUDE.md`, `reference/ptz_control_CLAUDE.md` | respective repo | Full-text copy of the source rules/history, basis for the rules in `CLAUDE.md` |
| `docs/specs/` | both repos (identical set) | Official Panasonic interface-spec PDFs — source of truth for every camera command |

## AK-UB300 restored, hidden from dropdown only + matrix_type/adaptive_matrix catalog gap fixed (2026-08-07)

AK-UB300 had been fully removed in commit `665582f` ("Reorder model dropdown, remove AK-UB300").
Per request it should stay out of the model dropdown for now (might be needed again later), but
the underlying code should stay available — restored `emulator/models/ak_ub300.py` verbatim plus
its 3 removed/adjusted tests, and excluded it from `server.py`'s dropdown-facing `MODEL_IDS` via a
new `_HIDDEN_FROM_DROPDOWN` set (still resolvable via `get_registry().resolve("AK-UB300")` for
scripts/tests). 49/49 tests pass (46 + the 3 restored).

Separately, cross-testing every `smart_reset_work` Panasonic model's real reset sequence against
this emulator (using `smart_reset_work`'s own, unmodified `ResetEngine` over a real HTTP round
trip, one model at a time) surfaced that 11 models' catalogs here were missing `matrix_type`
(`OSE:31`) and `adaptive_matrix` (`OSJ:4F`) — both spec-confirmed valid commands that
`smart_reset_work`'s `RESET_COMMANDS` already use for these models, just never ported here. Added
to `aw_he120.py`, `aw_he130.py`, `aw_he40.py` (covers `aw_he42`/`aw_ue70` via re-export),
`aw_hr140.py`, and `aw_ue80.py` (covers `aw_ue30`/`aw_ue40`/`aw_ue50` via re-export), plus
`aw_ue100.py` — same dropdown/toggle shape and command values already used by `aw_ue150.py`.

Re-verified after both fixes: all 16 comparable `smart_reset_work` Panasonic models (AW-UE145
excluded — known identity mismatch, see `smart_reset_work`'s own CHANGELOG.md) now complete their
real reset sequence against this emulator with zero errors, up from 4/16 before this change. This
also surfaced two genuine bugs on the `smart_reset_work` side (AK-UB300 sending `OGU`/`OSE:31`
commands it doesn't actually support) — fixed there, not here; see that repo's own CHANGELOG.md.

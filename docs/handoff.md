# ARINC 653 Lab handoff — 2026-11-17

The repository began empty (unborn `work`, no HEAD); the prototype files are included in the initial GitHub publication to `main`
requested by the user. No separate ChatGPT conversation was accessed. This document
and repository files can be transferred independently.

Implemented a working Linux feasibility backend: editable partition A/B C modules,
strict version-1 JSON project/kernel/partition/channel configuration, CMake build,
C++17 owned-child supervisor and Python JSON Lines CLI. Airbus a653lib native
APEX subset is vendored unchanged at commit
`cbf17245fcf56deaafe8ef2f1c78814dee8238ad`. Original LGPL-2.1-or-later notices,
license text and hashes are under `third_party/`; its README license summary
conflicts with explicit library notices, so those notices govern our treatment.
Upstream launcher/shared-memory code is replaced by adapter hooks, not rewritten
APEX. No proprietary or downloaded AEEC header archive is included.

Run from repository root:
```
export PATH="/workspace/.tools/cmake/data/bin:$PATH"
python3 backend/cli.py build
python3 backend/cli.py run
python3 -m unittest discover -s tests -v
```

Verified on ordinary x86_64 Linux: clean build in a path with spaces, real C
message delivery (three repeats), edited C message after rebuild, invalid config
rejection, JSON parsing, protocol start/stop/restart/shutdown, unsupported Pause/
Step rejection, exit 7/SIGSEGV detection, bounded no-APEX infinite loop, Linux
stopped-state observation between windows and owned-child cleanup. All 6
integration tests pass, including a three-partition configuration. Windows/WSL and Qt were not tested.

Execution uses host time and internal SIGSTOP/SIGCONT on one available CPU.
There is no deterministic virtual time, user pause/step, exact real-time boundary,
source debugging, full process/port tracing, compliance or isolation guarantee.
Trusted applications use one aperiodic worker and ASCII report text. Upstream
queue timeouts/other services are incomplete; raw APIs bypass helper constraints.

Next: harden the limited facade and schema, add state/capability discovery, then
validate Windows/WSL transport. Reference ARINC revision remains open. Qt 6 Widgets
is preferred/proposed; POK was inspected at
`b2e1cc382f86adba47cb93f015d92bc2d11cf40e`, not built or integrated.

Cloud install/start instructions were saved as a draft; publication and new-task
restoration are not verified.

Relevant: `README.md`, `backend/`, `examples/two-partitions/`, `tests/`,
`docs/architecture.md`, `docs/semantics.md`, `docs/backend-evaluation.md`,
`docs/decisions.md`, `docs/status.md`, `docs/roadmap.md`, root `AGENTS.md`.

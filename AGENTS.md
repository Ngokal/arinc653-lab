# ARINC 653 Lab

Windows development/simulation product; the feasibility backend runs on Linux
and is intended for Ubuntu in WSL 2. Repository files are the shared source of
truth across Codex and a separate architecture chat. Do not assume access to it.

- `backend/`: strict configuration loader, Python CLI, C++17 supervisor, C helpers.
- `examples/two-partitions/`: editable C sources and schema-1 JSON configuration.
- `third_party/a653lib/`: pinned, unmodified LGPL library sources/headers.
- `tests/`: real build/run integration experiments.
- `docs/`: current architecture, decisions, evidence, status and handoff.

Verified commands, from repository root (CMake >=3.23 on PATH):
```
python3 backend/cli.py build
python3 backend/cli.py run
python3 -m unittest discover -s tests -v
```
Cloud CMake path: `/workspace/.tools/cmake/data/bin`.
Each cloud task is already isolated: reuse its checkout; do not create a Git
worktree unless the user explicitly requests one. Preserve existing changes.
Use English identifiers, comments and documentation; communicate with the user
in Turkish. Future UI labels are Turkish. Keep stdout JSON-only. Use structured
subprocess arguments, bounded experiments and owned-child cleanup. Preserve
third-party notices; do not infer standard behavior or hard real-time guarantees.
Update status/handoff after meaningful work; keep handoff approximately <400 words.

Read [architecture](docs/architecture.md), [semantics](docs/semantics.md),
[evaluation](docs/backend-evaluation.md), [decisions](docs/decisions.md),
[status](docs/status.md), [roadmap](docs/roadmap.md), and [handoff](docs/handoff.md).

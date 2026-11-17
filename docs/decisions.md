# Decision register

Date for all initial entries: 2026-11-17. No access to the user's separate
ChatGPT architecture conversation is assumed. History is retained here; future
replacements must mark old entries superseded and link the replacement.

| ID | Status | Decision | Basis | Rationale and consequences |
|---|---|---|---|---|
| D001 | accepted | Windows desktop GUI, initially Ubuntu in WSL 2 backend; ordinary Linux development supported | user instruction | Separate OS responsibilities; Windows integration still requires validation |
| D002 | accepted | GUI/backend separation and versioned command/event contract; GUI never mutates backend state directly | user instruction | Enables wsl.exe transport and alternate backends; CLI first |
| D003 | accepted | Initial one CPU model; example two partitions but model supports variable counts | user instruction | Supervisor selects one allowed host CPU; JSON allows 1–10 partitions |
| D004 | accepted | Readable versioned file configuration separates manifest, kernel, partitions, connections | user instruction | Strict fields, one channel size/capacity authority, generated native adapter |
| D005 | accepted | Partition applications are actual editable C sources; build and run from CLI | user instruction and experiment | C modules in separate child processes validate source-edit workflow |
| D006 | accepted | One logical address space and initialization entry per partition in initial profile | user instruction | Profile constraint, not a universal RTOS rule; no memory isolation claim |
| D007 | accepted | No source-level debugger, full compliance, certification, hard real-time or target-performance claims | user instruction | Scope and evidence limitations must stay visible |
| D008 | accepted | Evaluate a653lib first; actual-kernel emulator may be another backend later | user instruction | a653lib native selected experimentally; no T2080/custom FPGA assumptions |
| D009 | accepted | C++17/CMake preference for adapter/shared code; do not rewrite upstream backend | user instruction | C++ runner, CMake native subset, small Python config/protocol control plane |
| D010 | accepted | Use a653lib commit cbf17245fcf56deaafe8ef2f1c78814dee8238ad native subset unchanged, custom owned-process supervisor/storage hooks | experimental evidence | Message delivery works; upstream demo ownership/affinity/shared-key problems avoided, source retained under LGPL |
| D011 | accepted | Host-time functional profile and internal Linux signal windows; reject user Pause/Step | experimental evidence | No-APEX loop can be stopped and cleaned; no deterministic time or exact boundary latency |
| D012 | accepted | English code/docs and handoff, Turkish user communication/future UI labels | user instruction | Shared docs transfer independently of chat state |
| D013 | proposed | Qt 6 Widgets for future Windows GUI | user preference; not evaluated | Preferred direction; no toolkit integration or packaging experiment yet |
| D014 | proposed | POK as actual-kernel backend on a supported emulated target | proposal after source inspection | Requires target/toolchain, license audit, boot and semantic tests; not built |
| D015 | proposed | Choose reference ARINC 653 revision and normative service subset | open user input in prompt | No revision supplied; must precede conformance-oriented behavior work |
| D016 | proposed | Define encoding/binary payload contract, richer state snapshots and safe full APEX validation | prototype evidence | ASCII helper trace and trusted inputs are insufficient for a general product |

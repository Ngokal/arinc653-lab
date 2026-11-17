# Backend feasibility evaluation — 2026-11-17

## Airbus a653lib: selected for a constrained native prototype

Repository: https://github.com/airbus/a653lib
Inspected/pinned commit: `cbf17245fcf56deaafe8ef2f1c78814dee8238ad`.
Reviewed README, LICENSE.md, COPYING.LGPLv2.1, CMakeLists, public headers,
partition/process/queuing/time/shared-memory/scheduler implementations.
Vendored `a653_inc` and `a653_lib` trees are unchanged from that commit.
`third_party/a653lib/SHA256SUMS` records their file hashes.

The README ends with Apache-2.0 OR MIT, but LICENSE.md and library file notices
explicitly state LGPL-2.1-or-later; the CMake file itself has Apache/MIT notices.
Use LGPL-2.1-or-later for the copied library and retain original notices/source.
We do not rely on the README's conflicting general label. No AEEC archive or
proprietary/vendor header was downloaded or redistributed. The selected public
headers are included in upstream under its library notices; this is not a legal
opinion or permission for unrelated standard documents. See third-party notices.

Native upstream dependencies: C99/POSIX pthread/semaphore, SysV SHM, CMake >=3.23,
awk/sed and an externally downloaded ARINC header archive for additional interfaces.
Wasm adds WAMR/Wasmtime/WASI/Rust tooling and is not evaluated or built here.
We chose the smallest needed native library subset; its includes do not require
the external archive. GCC compilation/link and real queue delivery verified this
resolution. We did not build the full upstream demo or bypass TLS/checksums.

Specific upstream integration obstacles and resolution:

- `main.c` shutdown uses `system("pkill -9 <name>")`: unsafe ownership scope.
- `a653_i_sync.c` assumes CPUs 0 and last system CPU are available, splits a
  command string, and has an initialization index access after its partition loop.
- `a653_i_shm_if.c` uses a shared HOME-based ftok key, unsuitable for concurrent runs.
- Process and queue APIs have partial semantics, stubbed operations, unsafe raw
  arguments, cooperative mutex assumptions and ignored timeout parameters.

Inspected supported alternatives: a custom config and supervisor avoids the first
three without altering library sources. Only required native files are compiled;
shared-memory allocation and debug hooks are supplied by the adapter. This is not
a replacement kernel/runtime: APEX process creation, startup, partition mode and
queue data operations still execute upstream C functions. The adapter bounds and
observes trusted applications, while exposing the limited semantics explicitly.
The two C applications create one aperiodic worker each; a gate delays its body
until the partition's execution window. Upstream's unmodified aperiodic START would
otherwise run immediately. We avoid its periodic mutex scheduling path.

Observed: repeatable payload delivery in three normal runs; changed C payload
arrives after rebuild; exit 7 and SIGSEGV fail the run while controller survives;
an infinite worker with no APEX calls is stopped between windows, times out,
and is killed/reaped. These are functional results, not timing determinism.

## POK: future actual-kernel candidate, not integrated

https://github.com/pok-kernel/pok inspected at
`b2e1cc382f86adba47cb93f015d92bc2d11cf40e` (shallow checkout).
README, root LICENSE, Makefile, `misc/` build organization and example/kernel
layout reviewed. Root LICENSE is a two-condition BSD-style license; individual
files/dependencies require a full audit before integration. It is an embedded
microkernel with kernel, libpok, deployment examples and platform-specific build
machinery. It would require a selected supported emulated target/toolchain and
boot experiments, not just linking the host adapter. No POK build, execution,
T2080 support, custom FPGA emulation or timing behavior is claimed. It remains
proposed, outside this experiment. Optional ARISS/a653rs references were not
needed and were not evaluated.

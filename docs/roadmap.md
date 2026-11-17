# Roadmap

| Phase | State | Deliverables | Exit criteria |
|---|---|---|---|
| Functional feasibility | completed | Pinned a653lib evaluation, C sender/receiver, JSON config, native adapter/CLI, trace and Linux experiments | Clean build, real message, edited C message, invalid-config rejection, failure/loop cleanup verified |
| Behavioral and protocol hardening | planned | Schema artifact, structured process/port snapshots, validation around unsafe raw APEX paths, binary/Unicode representation, stronger initialization/timeout contracts | Documented service profile with negative tests and explicit capability discovery |
| Windows integration | planned | WSL 2 Ubuntu build/run proof, argument/path transport checks, basic Qt 6 Widgets client | Same success scenario from Windows; reconnect/shutdown and failure reporting validated |
| Configuration/source editor | planned | Turkish UI, kernel/partition/address-space/channel views, actual C editor and build diagnostics | File roundtrip, strict validation and source edit/build/run observable through backend only |
| Execution exploration | planned | Capability-based time controls and event/state inspection | Commands accurately match backend abilities; unsupported controls remain disabled/rejected |
| Actual-kernel feasibility | planned | POK or another evaluated kernel on an explicitly supported emulated machine | Reproducible boot/message scenario, target/license/toolchain evidence; no invented board support |

No work beyond the functional feasibility phase is marked complete. The current
prototype is a development feasibility baseline; normative semantics, security
isolation and deterministic simulation remain separate work.

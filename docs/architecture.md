# Architecture and contract v1

Future Windows Qt 6 Widgets GUI -> wsl.exe stdio transport -> Linux Python CLI
-> C++17 runner -> separate forked partition processes -> C application modules
and a653lib APEX services. No GUI is implemented. Build tools use argument arrays.
The controller never loads application code itself. Forked children use dlopen
on C modules; they are not freestanding RTOS executables. a653lib is a replaceable
shared library, with full corresponding vendored source and notices.

`config.py` is the executable schema-1 validator and native configuration adapter.
The manifest references separate kernel, partition and connection JSON files.
Unknown fields are rejected at every defined object. Channel message size and
capacity have one authority (channel); endpoints inherit them. `lab_port` makes
runtime CREATE calls from that definition when invoked by a C application's
initialization entry. Static declarations alone do not create the runtime port.
Generated `config.c` and `partitions.cmake` live only in the build directory.
Sources must stay below the manifest directory; CMake special path characters
are rejected. Paths containing ordinary spaces were tested.

One private anonymous MAP_SHARED region holds upstream structures and FIFOs;
no global SysV key, HOME override or shared temporary key file. The supervisor
forks configured partitions, pins itself/children to one available Linux CPU,
waits for initialization, and gates workers until all initialization is complete.
It then alternates SIGCONT/SIGSTOP with acknowledged stops, using host-time
windows. Idle windows retain their duration. Exited partitions are not restarted.
The timeout includes initialization. Any nonzero/signal exit fails the run and
kills/reaps remaining owned PIDs. SIGTERM/INT requests cleanup; children have
Linux parent-death SIGKILL and the runner has parent-death SIGTERM. CLI fallback
kills only its private process group. Applications are trusted and must not fork
additional descendants; this is not an adversarial sandbox.

## Public JSON Lines protocol

Launch `python3 backend/cli.py serve` after building. Each stdin line is exactly:
```json
{"schema_version":1,"id":"request-1","command":"start"}
```
Commands: `start`, `stop` (idempotent), `status`, `shutdown`. Only one run at a
time. EOF shuts down. `pause`, `resume`, `step` and unknown commands return
`command_result` with `ok:false`; they never report false success. IDs are echoed.
`start` acknowledges launch, not successful application completion. Observe
`backend_exit.code` and `run_finished` for completion/failure. `status.running`
reports the runner's OS-process liveness, not partition readiness. Build/validate
are CLI operations outside this command protocol.

Each stdout line has `schema_version:1`, `event`, `clock:host_monotonic`, and
`host_time_ns`. Time is stamped by the CLI when relaying the event, not at exact
application execution; there is no virtual timestamp. Events include
`backend_ready`, `command_result`, `partition_started`, `port_created`,
`process_created`, `partition_mode`, `process_running`, `message_sent`,
`message_received`, `window_open`, `window_closed`, `partition_exit`,
`partition_cleaned`, `timeout`, `run_finished`, `backend_exit`, `error`.
Runner events carry a zero-based `partition_index` (-1 for run scope), emitter
`pid`, message and code. `partition_started.code` is the child PID;
`partition_exit.code` is exit status or 128+signal. Other code fields are status
values (usually zero). Order of independent initialization events may vary.
`partition_mode` is a NORMAL request notification, not a full state snapshot.
C `lab_report` emits bounded text events; byte values >=127 are escaped individually
(the initial text profile is ASCII). Raw binary messages and arbitrary Unicode
need a later encoding contract. Application and dependency diagnostic stdout is
redirected to stderr. Port/process events are helper instrumentation, not a
complete trace of all raw upstream APEX calls.

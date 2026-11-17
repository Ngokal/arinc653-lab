# Behavior profile a653lib-native-host-v1

Schema version 1 is implemented by `backend/config.py`. Exactly one logical
address space and initialization entry per partition, 1–10 partitions, one
application worker requested through `lab_start`. The data model does not assume
two partitions. The example uses two. Channel count 1–59; up to 44 local ports,
message size 1–1500 bytes, queue capacity 1–40. Every endpoint has exactly one
connection; queuing FIFO unicast only. Sampling, refresh periods, memory budgets,
priority scheduling and extra fields are rejected, rather than silently modeled.
Kernel max_partitions is an admission limit; the one-worker field describes the
helper profile. Raw upstream APIs can bypass the helper and are not sandboxed.
The supervisor enforces no arbitrary memory limit. Linux process address spaces
exist but shared APEX memory is writable; neither logical address-space names nor
configuration imply MMU-enforced ARINC isolation. Initialization runs before the
partition-window schedule; application worker bodies run only after the gate.

## Execution capabilities

| Capability | Status | Evidence / scope |
|---|---|---|
| Functional host-time execution | supported | Compiled C payload sent/received through upstream queue |
| Deterministic virtual time | unsupported | Host sleeps, pthreads and OS signals; no virtual clock |
| Stop at partition boundaries | supported | Adapter SIGSTOP + waitpid stop acknowledgment; loop experiment observes Linux T state during B window |
| Exact deadline/window timing | unsupported | Host jitter and signal latency; no real-time guarantee |
| Intra-partition priority preemption | unverified | Upstream pthread priority request unchecked; only one worker tested |
| User pause/resume | unsupported | Protocol rejects commands; scheduling SIGSTOP is internal only |
| Advance to next simulation event | unsupported | No event-driven time engine; step rejected |
| Source debugger stepping | unsupported | Outside task; no debugger integration |
| Full process/port trace | unsupported | Helper events exported, raw APEX calls not universally intercepted |
| Application failure containment | supported | exit 7 and signal 11 observed/reaped; controller reports failure |
| Repeatability of payload | supported | Three independent normal runs and source-change test |
| Repeatable event interleaving/timestamps | unsupported | Host scheduling and relay timestamps vary |

## Evidence-based APEX service matrix

This table concerns the selected upstream subset plus stated adapter constraints,
not conformance to an unspecified standard revision.

| Services | Support/evidence | Limitations |
|---|---|---|
| SET_PARTITION_MODE(NORMAL) | supported in example | Upstream blocks main on semaphore; helper reports request, adapter releases worker gate |
| GET_PARTITION_STATUS | implemented, unverified in execution | Upstream static status fields; not a full accurate state model |
| Other mode transitions | unverified | Not used/tested; no lifecycle guarantee |
| CREATE_PROCESS, START | supported through lab_start | One aperiodic worker, trusted attributes; raw API unsafe for arbitrary IDs/counts |
| STOP/STOP_SELF, SUSPEND/RESUME, SET_PRIORITY | unsupported for this profile | Upstream stubs/NO_ACTION; runner termination is Linux process control |
| CREATE_QUEUING_PORT | supported through lab_port | Static definition feeds runtime CREATE; receiver creates FIFO during init; prefix-match upstream lookup avoided by exact helper lookup |
| SEND_QUEUING_MESSAGE | supported, tested | Nonblocking only; timeout ignored upstream; not all argument/direction validation is correct |
| RECEIVE_QUEUING_MESSAGE | supported, tested | Nonblocking empty yields upstream NO_ACTION; C receiver polls using host usleep |
| Queue status/clear | unsupported | Upstream NO_ACTION stubs |
| GET_TIME | implemented, unverified in execution | CLOCK_REALTIME minus bootTime; not event clock or virtual time |
| TIMED_WAIT | unsupported as normative service | Upstream host usleep, leaves return code unset; example deliberately uses explicit usleep |
| PERIODIC_WAIT | unverified/unused | Upstream cooperative mutex path; no process-preemption guarantee |
| Sampling / other APEX services | unsupported by profile | Some upstream implementations exist, outside validated scope |

No normative return-code/timing claims are inferred from API names. Reference
ARINC 653 standard revision and required normative subset remain open decisions.

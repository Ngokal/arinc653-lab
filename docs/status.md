# Status — 2026-11-17

## Inspected revision and working tree

Local repository was an unborn `work` branch: no HEAD commit existed, no tracked
files, no initial uncommitted files, and no AGENTS.md. Earlier read-only remote
inspection found an empty GitHub repository. This task adds all prototype sources,
configuration, tests, third-party sources and documentation as untracked files;
the prototype was initially prepared without a commit or push. The user
subsequently requested publication to GitHub; these files are being included in
the initial commit on remote `main`. `build/` and Python caches are ignored.
No pre-existing work was overwritten. Upstream inspected revisions are recorded
in backend-evaluation.md and third_party/NOTICE.md.

## Working and validated on ordinary Linux

x86_64 Linux, GCC/G++ 14.2.0, Python 3.12.14, CMake 3.31.6 installed locally.
- Clean CMake configure/build in a temporary path containing spaces succeeds.
- Actual partition C applications deliver a queuing message using a653lib.
- Editing sender C source, rebuilding and rerunning changes receiver output.
- CLI stdout parses as JSON Lines with version and explicitly host-time fields.
- Unknown config fields and inconsistent major-frame duration are rejected.
- CLI command startup, stop, restart and shutdown succeed; pause/step reject.
- Exit 7 and SIGSEGV detected; controller survives and reports failed run.
- No-APEX infinite loop crosses multiple windows, is observed in Linux stopped
  state during another partition's window, hits deadline, then is killed/reaped.
- A three-partition configuration also builds/runs and retains message delivery.
- Child PIDs from bounded run experiments are absent after completion.

Actually executed:
```
sh scripts/setup.sh
python3 backend/cli.py validate
python3 backend/cli.py build
python3 backend/cli.py run
python3 -m unittest discover -s tests -v
```
The integration suite has 6 tests, all passing (multiple delivery runs, modified
message, exit/signal/loop experiments, invalid-config variants and protocol flow
inside those tests). CMake PATH setup is documented in README. Validation logs
are summarized here; transient raw logs were under /tmp, not a required artifact.
Upstream vendored files were byte-compared with the pinned checkout before
SHA256SUMS was generated.

## Not executed / limitations

Windows/WSL, Qt, actual RTOS boot, full upstream demo/Wasm build, source debugging,
full APEX/standard conformance, adversarial process trees, arbitrary multi-worker
preemption and target timing were not tested. Sampling is rejected by the profile.
Host timing is nondeterministic; raw upstream APIs have validation and return-code
defects (see semantics.md). Queue timeout and full state/port tracing are missing.
Only trusted application code is supported, with one helper worker per partition;
calling raw APIs can bypass profile resource expectations. Event text is ASCII.
Run executes last built artifacts; it does not auto-detect/rebuild edited sources.
No active external network/dependency blocker remains for this Linux workflow.

## Next task and open decisions

Next: harden the limited APEX facade/config schema and add structured state and
capability discovery before a minimal Windows/WSL transport proof. Choose the
reference standard revision and required normative subset before claiming any
standard behavior. Qt and an emulated actual-kernel target remain proposed.

## Reusable cloud configuration

Saved `install_script` and `start_skill` in the environment draft. They record
`scripts/setup.sh`, PATH activation, build/run/test checks and the stdio startup
contract. Saving does not execute, apply or publish configuration. Current Linux
commands were executed independently; a new-task restoration has not been tested.
The user can review/save these settings and publish the prepared environment.

# ARINC 653 Lab feasibility prototype

Runs real C partition applications using an unmodified native subset of Airbus
a653lib, a C++17 Linux supervisor, and a Python JSON Lines CLI. No GUI yet.
This is a functional experiment, not a compliance, certification, hard real-time,
security isolation, or target-performance claim.

## Ordinary Linux (verified on x86_64 Linux)

Requires Python >=3.10, GCC/G++, pthreads, GNU Make and CMake >=3.23.
In this cloud machine CMake 3.31.6 was installed under `/workspace/.tools` using
`scripts/setup.sh`. The compiler is GCC 14.2.0. No service, credential or network
access is needed to build after tools are installed; library sources are vendored.

```sh
# From the repository root; with cmake on PATH:
python3 backend/cli.py validate
python3 backend/cli.py build
python3 backend/cli.py run
python3 -m unittest discover -s tests -v
```

On the prepared cloud machine, first use:
```sh
export PATH="/workspace/.tools/cmake/data/bin:$PATH"
```

The `message_received` JSON event contains `Hello from partition A`.
Change that string in `examples/two-partitions/partition_a.c`, then run the build
and run commands again. The receiving application reports the new string.
The integration suite performs this edit/rebuild experiment in a temporary copy.
Build logs and application stdout go to stderr; CLI stdout contains JSON only.
Build failures return nonzero. Run timeout defaults to 3000 ms and returns nonzero.
Use `--timeout-ms 500` for a shorter bounded run. Options `--project PATH` and
`--build-dir PATH` allow a different project and build directory. Rebuild after
any configuration/source change; run uses the last built artifacts.

## Windows with WSL 2 / Ubuntu (instructions, not validated here)

Install WSL 2 and Ubuntu through Windows, then inside Ubuntu:
```sh
sudo apt-get update
sudo apt-get install -y build-essential cmake python3 git
cd ~/src/arinc653-lab
python3 backend/cli.py build
python3 backend/cli.py run
```
Check `cmake --version` is >=3.23. Keep builds on the Linux filesystem for normal
Linux file permissions and performance. `C:\\work\\arinc653-lab` maps to
`/mnt/c/work/arinc653-lab`. `~/src/...` inside WSL has no equivalent `C:` path;
Windows can browse it through `\\wsl.localhost\\Ubuntu\\home\\USER\\src\\...`.
All paths in project JSON are relative to the project manifest's Linux directory;
JSON does not accept a Windows path as a Linux source path.

A future GUI should launch a structured argument array equivalent to:
`["wsl.exe", "--distribution", "Ubuntu", "--cd", "/home/USER/src/arinc653-lab", "--", "python3", "backend/cli.py", "serve"]`.
It should read stdout events, show stderr diagnostics separately, and send
versioned commands through stdin. Never concatenate configuration into shell code.
Qt, wsl.exe, Windows packaging and this invocation remain untested.

## Documentation

- [Architecture and protocol](docs/architecture.md)
- [Backend and license evaluation](docs/backend-evaluation.md)
- [Behavior profile and service matrix](docs/semantics.md)
- [Decisions](docs/decisions.md), [status](docs/status.md), [roadmap](docs/roadmap.md)
- [Cross-session handoff](docs/handoff.md)
- [Third-party notices](third_party/NOTICE.md)

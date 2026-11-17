# Third-party notices

## Airbus a653lib

Source: https://github.com/airbus/a653lib
Pinned commit: cbf17245fcf56deaafe8ef2f1c78814dee8238ad
Copyright (c) 2022–2023 Airbus Defence and Space (see individual files).
Library license: GNU Lesser General Public License, version 2.1 or later.

The unmodified `a653_inc/` and `a653_lib/` source trees are redistributed here,
with original file notices, upstream LICENSE.md and COPYING.LGPLv2.1. Hashes in
SHA256SUMS identify the files. Only the subset listed in root CMakeLists.txt is
compiled, into `libapex.so`; applications/controller link dynamically. Full
corresponding source for that library subset is present and rebuildable. The
adapter provides storage/debug hooks rather than modifying upstream files.
Do not strip license notices or replace this library with a non-replaceable
binary distribution without reviewing LGPL obligations. The upstream README
and library license labels conflict; we retain and use the explicit library
file notices and LICENSE.md, not the README's Apache/MIT summary.

Dependencies used here: host C/C++ runtime and POSIX/Linux APIs, Python 3,
CMake and Make/GCC toolchains. These system tools are not vendored. No Wasm
runtime, external AEEC header archive, POK code or proprietary vendor library is
included. POK was inspected only; its root two-condition BSD-style license and
individual notices need a full audit before a future integration.

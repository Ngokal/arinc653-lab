#!/bin/sh
# Run from the repository root. Dependencies are retained outside the checkout.
set -eu
python3 -m pip install --target /workspace/.tools cmake==3.31.6 --upgrade >&2
export PATH="/workspace/.tools/cmake/data/bin:$PATH"
python3 backend/cli.py build

#!/usr/bin/env bash
# Create .venv and install the dependencies: `./mkvenv.sh`
# Re-running it is safe: an existing .venv is reused and just brought up to date.
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo
echo ".venv is ready -- start the dev server with: source run.sh"

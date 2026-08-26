#!/usr/bin/env bash
# Source this to run the Flask dev server: `source run.sh`
cd "$(dirname "${BASH_SOURCE[0]}")" || return
source .venv/bin/activate
mkdir -p data
python3 runserver.py

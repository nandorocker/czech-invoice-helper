#!/bin/bash
# Alfred workflow wrapper for czk-exchange.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "$SCRIPT_DIR/../czk-exchange.py" --alfred --alfred-query "$1"

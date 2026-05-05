#!/bin/bash
# Alfred workflow wrapper for czk-exchange.py
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -n "$1" ]; then
    python3 "$SCRIPT_DIR/../czk-exchange.py" --alfred -c "$1"
else
    python3 "$SCRIPT_DIR/../czk-exchange.py" --alfred
fi
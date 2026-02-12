#!/usr/bin/env bash

set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  ./run.sh [cli|web]

Examples:
  ./run.sh cli
  ./run.sh web
EOF
}

mode="cli"

if [[ $# -gt 1 ]]; then
    echo "Error: expected at most one argument: cli or web" >&2
    usage
    exit 1
fi

if [[ $# -eq 1 ]]; then
    mode="$1"
fi

if [[ "$mode" != "cli" && "$mode" != "web" ]]; then
    echo "Error: mode must be 'cli' or 'web', got '$mode'" >&2
    usage
    exit 1
fi

uv run python -m src.main --mode "$mode"

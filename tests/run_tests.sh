#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESULT_DIR="$PROJECT_ROOT/test-results"
mkdir -p "$RESULT_DIR"

if [[ -z "${PYTHON:-}" ]]; then
    if [[ -x "$PROJECT_ROOT/wsl_conversion_box/bin/python" ]]; then
        PYTHON="$PROJECT_ROOT/wsl_conversion_box/bin/python"
    elif [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
        PYTHON="$PROJECT_ROOT/.venv/bin/python"
    else
        PYTHON="python3"
    fi
fi

TIMESTAMP="$(date +"%Y%m%d-%H%M%S")"
RESULT_FILE="$RESULT_DIR/test-$TIMESTAMP.xml"

cd "$PROJECT_ROOT"
"$PYTHON" -m pytest -v --junitxml="$RESULT_FILE"

echo ""
echo "Test results saved to: $RESULT_FILE"
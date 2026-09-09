#!/bin/bash
set -euo pipefail
workspace="${TASK_WORKSPACE:-/app}"
cp "$(dirname "$0")/design.sv" "$workspace/design.sv"

#!/bin/bash
set -euo pipefail
workspace="${TASK_WORKSPACE:-/app}"
for name in design.sv map_bypass.sv ownership.sv; do
    cp "$(dirname "$0")/$name" "$workspace/$name"
done

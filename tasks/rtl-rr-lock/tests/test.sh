#!/bin/bash
set -uo pipefail
workspace="${TASK_WORKSPACE:-/app}"
logdir="${VERIFIER_LOG_DIR:-/logs/verifier}"
mkdir -p "$logdir"
printf '0\n' > "$logdir/reward.txt"
timeout_cmd="$(command -v timeout || command -v gtimeout || true)"
if [[ -z "$timeout_cmd" ]]; then printf "Missing timeout or gtimeout\n" > "$logdir/compile.log"; rm -f "$logdir/reward.txt"; exit 2; fi
for required in iverilog vvp; do
  if ! command -v "$required" >/dev/null 2>&1; then printf "Missing %s\n" "$required" > "$logdir/compile.log"; rm -f "$logdir/reward.txt"; exit 2; fi
done
testdir="$(cd "$(dirname "$0")" && pwd)"
if ! "$timeout_cmd" 30 iverilog -g2012 -s tb -o "$logdir/sim" "$workspace/design.sv" "$testdir/tb.sv" > "$logdir/compile.log" 2>&1; then exit 0; fi
if "$timeout_cmd" 30 vvp "$logdir/sim" > "$logdir/simulation.log" 2>&1 && grep -qx 'ALL_TESTS_PASSED' "$logdir/simulation.log"; then
  printf '1\n' > "$logdir/reward.txt"
fi
exit 0

# Harness and calibration protocol

> Target correction: the latest user instruction is **20% pass / 80% failure**. Earlier target statements below are historical. Existing frozen trials are unchanged; new candidate selection uses the corrected target.
The repository uses its own Python 3.11+ standard-library controller around Harbor tasks. Harbor performs isolated model execution; this controller validates the local task contract, checks oracle and starter behavior, creates independent trial commands, records outcomes, and computes uncertainty. It is not a replacement for Harbor's container orchestration.

The current primary target is **80% success / 20% failure per task** on `gpt-6-astra` at fixed `high` reasoning effort. The optional `hard` planning profile captures the example's 10–20% success target but is not the primary target. These are targets, not measured properties of the tasks.

## Commands

Run from the repository root. `python` must be Python 3.11+; on this machine `uv run --python 3.12 python` works.

```sh
python -m unittest discover -s tests -v
python -m harness.cli validate tasks/rtl-skid-flush tasks/rtl-rr-lock
python -m harness.cli oracle tasks/rtl-skid-flush tasks/rtl-rr-lock --out runs/native
python -m harness.cli baseline tasks/rtl-skid-flush tasks/rtl-rr-lock --out runs/native
python -m harness.cli trials tasks/rtl-skid-flush --trials 10 --effort high
python -m harness.cli trials tasks/rtl-skid-flush --trials 10 --effort high --execute --out runs/calibration
python -m harness.cli report runs/calibration/*.json
```

`trials` without `--execute` prints a JSON plan and does not invoke a model. Every trial gets a unique job directory, fresh Harbor environment and conversation, one attempt, and zero automatic retries. The campaign stops the remaining trials for a task at its first infrastructure error so a broken setup is not repeatedly retried. Only the Codex agent is used for model trials. Harbor receives the model string `gpt-6-astra` explicitly; an absent or different reported model quarantines the result as an infrastructure error. Current Harbor CLI arguments were accepted by local Harbor 0.22.0 using `--print-config`; that checks configuration, not credentials or model availability.

The native checks require `bash`, `iverilog`, and `vvp`. They copy only `environment/repo` into a temporary working directory and set `TASK_WORKSPACE` and `VERIFIER_LOG_DIR`. `oracle` runs `solution/solve.sh`, then `tests/test.sh`; `baseline` runs only the verifier. Test scripts should exit zero after a valid grading decision, emitting `reward.txt` containing exactly `0` or `1`. Nonzero script exits, missing rewards, and timeouts indicate an invalid native check. These are author-side smoke checks, not sandboxed execution of untrusted submissions. A passing oracle and failing baseline establish useful grader behavior, not model difficulty.

## Outcomes and statistical claims

Each executed trial produces one JSON record with a UUID, UTC start time, task SHA-256, requested model, effort, trial kind, command or native phase logs, and status. Task hashes cover every task file. Keep evaluation records outside task directories so creating records cannot alter the task hash.

- `success`: complete verifier result with binary reward 1.
- `model_failure`: complete verifier result with binary reward 0.
- `infra_error`: missing tools, invalid output, nonzero runner status, exceptions, or model identity mismatch. Excluded from the success/failure denominator.

All Harbor exceptions are conservatively quarantined, including ambiguous timeouts. A human must inspect the exception and trace before calling a timeout a model failure. Preserve the original record and document any adjudication separately. Do not silently relabel errors or replace unsuccessful valid trials.

Reports group by task, task hash, requested model, effort, and kind. They reject duplicate UUIDs and unknown statuses, and return null rates for zero valid trials. Native oracle/baseline records are kept in separate groups and must never be interpreted as model performance. Use only the top-level record JSON files as report inputs, not nested Harbor job results.

Ten independent trials are an initial screen. An observed 8/10 success has a 95% Wilson success interval of approximately **49.0–94.3%**, or failure interval **5.7–51.0%**. It cannot establish a precise 20% failure rate. Use additional fresh confirmation trials after tuning, retain all valid runs, freeze task/version and grading before confirmation, and report both count and interval. Do not pool changed tasks, different reasoning efforts, or model versions. The target is per-task; a suite average can hide tasks that are trivial or impossible.

## Isolation, limitations, and reproducibility

Harbor uploads the solution directory for oracle runs and verifier assets during verification. For model trials, the Docker build context must contain only starter files and dependencies; never copy the task root, solution, author notes, or hidden tests into the agent environment. The local controller does not itself enforce Dockerfile information-flow security or full Harbor schema compatibility. Review the image build context and run Harbor's own validation before calibration. Hidden tests are grading assets, not a substitute for an explicit public behavioral contract.

A real trial requires a working Docker daemon, Harbor, a compatible Codex agent installation, and authorized credentials for the exact model. A running model inside this desktop task does not by itself establish that Harbor can call the same model. There is no fallback model. The controller does not access credentials directly; Harbor/Codex handles credentials through its supported setup. A controller timeout may require inspecting and cleaning up the associated Harbor containers before retrying.

Record the Harbor/Codex versions, container digest, dependency versions, resource limits, timeout settings, sampling configuration, and credential route with each calibration campaign. Harbor's nested config/trajectory files preserve further execution details. The current controller records the requested effort; reviewers should confirm the effective configuration in Harbor's trial config. No model trials are implied by native tests or command planning.

Official references checked September 9, 2026: [task format and special paths](https://www.harborframework.com/docs/tasks), [evaluation layout](https://www.harborframework.com/docs/run-jobs/run-evals), [agent kwargs](https://www.harborframework.com/docs/agents), and [trial result schema](https://github.com/harbor-framework/harbor/blob/main/src/harbor/models/trial/result.py).

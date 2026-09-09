# Trial execution report

Updated 2026-09-09T21:23:52.327612+00:00. Status: **infra_blocked**. Current target: **20% pass / 80% failure per task** on `gpt-6-astra`, reasoning effort `high`. Ten independent trials per task are the initial screen. These campaigns launched under the superseded target of 20% failure / 80% pass; the user corrected the desired target during execution. Tasks and execution settings remain frozen.

| Task | Valid | Successes | Failures | Infrastructure errors | Observed pass | 95% Wilson pass interval | Observed failure | 95% Wilson failure interval |
|---|---:|---:|---:|---:|---:|---|---:|---|
| rtl-rr-lock | 6 | 6 | 0 | 1 | 100.0% | 61.0–100.0% | 0.0% | 0.0–39.0% |
| rtl-skid-flush | 10 | 10 | 0 | 0 | 100.0% | 72.2–100.0% | 0.0% | 0.0–27.8% |

These counts describe this frozen task version and configuration. Ten runs provide a noisy screen, not a precise underlying failure probability. An observed 8/10 success has a failure interval of approximately 5.7–51.0%. No unsupported failure-mode labels are inferred from aggregate counts.

The initial skid-buffer pilot `3b833baa-9c7d-4d6a-8795-ed41d6c05109` was operator-cancelled during dependency setup before model execution, to allow grader fixes without task-version contamination. It is an infrastructure error, excluded from calibration and retained unchanged in `work/pilot` with hash `c0990619dd759ff7b06a706b29eafcb63e9aa79f123bc4bfc31c1bbb9f876e58`. Revised-task outcomes are never pooled with that version.

Tasks froze after expert review at commit `303f494`; exact hashes, sanitized trial IDs/outcomes, settings and evidence paths are in [trial-summary.json](trial-summary.json). Each run gets a fresh container/conversation, one attempt and zero automatic retries. Any infrastructure exception halts further runs of that task. Original records and raw logs remain in ignored `work/runs`; they have not been published.

Harbor 0.22.0 / Codex 0.153.4 / Node 22.23.2 / Icarus Verilog 11.0 / ripgrep 13.0.0 on Linux arm64. Base image manifest and Codex version are pinned. Effective execution explicitly selects `--model gpt-6-astra` and `-c model_reasoning_effort=high`; the reported model and agent version are checked. Temperature is not overridden. Agent timeout: 900 seconds; verifier: 120 seconds; resources: 1 CPU, 1024 MB memory, 2048 MB storage. Maximum campaign concurrency is two.

Harbor uses its supported `CODEX_FORCE_AUTH_JSON=1` authentication route. No credentials enter the images, reports or repository. Both final Docker oracle runs passed. Oracle outcomes and expert judgments are independent of model calibration and excluded from its denominator.

Harbor-reported cost for completed revised-task runs: $5.9628. This is runner metadata, not a billing statement.

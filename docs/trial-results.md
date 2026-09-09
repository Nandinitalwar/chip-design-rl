# Trial execution report

Updated September 9, 2026. Target: 20% failure per task on `gpt-6-astra`, reasoning effort `high`. Ten valid independent trials per task are planned; no valid model outcomes have completed yet. Success and failure rates are unknown.

The initial skid-buffer pilot (`3b833baa-9c7d-4d6a-8795-ed41d6c05109`) was stopped by the operator during dependency setup before model execution, while expert review prompted grader fixes. Harbor reported an infrastructure error. It is excluded from calibration and preserved under ignored `work/pilot`; its original task hash is `c0990619dd759ff7b06a706b29eafcb63e9aa79f123bc4bfc31c1bbb9f876e58`. It must not be pooled with revised tasks.

Agent dependencies are being cached into the task Docker images to avoid repeating slow installation in each independent trial. Codex is pinned to 0.153.4; Harbor is 0.22.0. Credentials use Harbor's supported `CODEX_FORCE_AUTH_JSON=1` route and are never baked into images or copied into this report. Raw jobs remain ignored under `work/`.

Calibration starts only after grader review and task-hash freeze. Each trial uses a fresh environment and conversation, one attempt, and zero automatic retries. Infrastructure exceptions are excluded from the denominator and preserved. The campaign stops on infrastructure failure rather than repeatedly spending runs on the same broken setup.

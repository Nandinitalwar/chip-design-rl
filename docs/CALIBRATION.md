# Calibration protocol

> Target correction: the latest user instruction is **20% pass / 80% failure**. Earlier target statements below are historical. Existing frozen trials are unchanged; new candidate selection uses the corrected target.
Confirmed target: 20% failure per task on GPT-6 Astra, or 80% single-trial success. This is an empirical target, not a selling requirement established by METR. Report task-level results as well as dataset-level totals.

## Frozen evaluation configuration

- Model: gpt-6-astra; retain returned model identifier when available.
- Reasoning effort: high (initial proposed default).
- Agent: Harbor Codex adapter, version recorded by run. Pin agent version before release.
- Harness: repository custom Python runner, Harbor 0.22.0 for container execution.
- Ten independent fresh trials per task for screening. No author context, reference oracle, previous attempts, or hidden tests in the agent workspace.
- Use each task's declared wall-clock limit. Record actual duration, tokens/cost when available, and infrastructure errors.
- Binary correctness reward; diagnostics explain behavior but do not invent partial credit.

## Interpretation

Eight successes out of ten estimate 80% success. A 95% Wilson interval is approximately 49%–94%; ten runs cannot demonstrate the true failure probability is exactly 20%. Success rate is distinct from pass@10 (probability that at least one of ten attempts succeeds).

Use ten runs to decide whether to retain or revise a task, then freeze its assets and collect an independent validation batch. Report both tuning and validation batches. Never select lucky runs. For a tighter estimate, predefine a larger sample and tolerance with the buyer; roughly 246 trials estimate p=0.8 within five percentage points at 95% using a normal planning approximation, not a guarantee.

## Attribution

Every task has an intended failure mechanism. Observed failures require evidence: failed test/check, relevant diff or artifact, and corroborating agent trace when available. Do not infer private reasoning or claim causation from the task label alone. Classify setup, service/authentication, dependency, and verifier defects separately. An agent exhausting its agreed task budget is a model outcome if infrastructure was healthy. Correct submissions rejected by a buggy grader invalidate the run and require grader repair plus reruns.

## Release gate

Oracle passes; starter fails for intended reasons; realistic defective implementations are rejected; prompt contains every scored requirement; grader is deterministic; container checks pass; task dependencies and provenance are recorded; independent model validation meets the agreed band. No task in this initial batch is yet marked calibrated or ready for sale.

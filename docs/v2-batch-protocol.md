# V2 bounded fresh-Astra batch

User-authorized scope: one redesigned candidate, five fresh attempts, then pause. Desired observed result is one pass and four failures; no guarantee or selective reporting. Budget is five total model attempts, not five successes at launching or five valid outcomes with unlimited replacement runs.

## Prelaunch gates

- Exact v2 contract and real starter reviewed independently.
- Oracle, valid alternative implementations, semantic negative controls and grader-boundary checks validated.
- Independent implementation/grader review closed; actual Harbor oracle preflight passed.
- Task hash frozen before any model attempt; do not edit the task during the batch.

## Execution

- Model gpt-6-astra, high effort, fresh Codex desktop task per attempt, no forked conversation history.
- Provide only exact public task instructions plus generic container-execution adapter. Do not reveal desired success rate, previous attempts, reviews, oracle or private tests.
- Each candidate gets a separate original starter container, node user, no host mounts or network; installed public tools and smoke only.
- Host tools are instructed to operate only through the assigned candidate container. This is protocol isolation, not removal of all desktop host-tool privileges; report separately from Harbor installed-agent runs.
- Nominal solving budget is the frozen task's agent timeout. Record actual duration and any enforcement limitation.
- Maximum two concurrent candidate attempts; no helpers or other-model calls inside a solver.
- Keep every attempt, including infrastructure and credit failures. Do not replace invalid attempts without new user authorization.
- After completion, copy the three submitted source files and grade once in a separate trusted verifier container. No grader feedback or repair loop to the solver.
- Preserve submitted file hashes, logs, exact task hash, worker IDs, settings, statuses and durations.

## Report and pause

Report each attempt and the valid-outcome denominator. A model success is deterministic functional+synthesis acceptance; candidate failure must be distinguished from infrastructure failure using grader status. Report unknowns explicitly. Five outcomes do not establish an exact underlying pass probability. Do not manufacture one success by weakening a grader, changing prompts midway, stopping after favorable outcomes or selecting runs.

Pause after five attempts, even if every attempt passes or fails. No second batch, task change followed by another evaluation, or additional model diagnosis is authorized by this batch instruction.

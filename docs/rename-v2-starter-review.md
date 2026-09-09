# V2 actual starter review

Date: 2026-09-09. Independent LLM judge. Scope: five candidate-facing files under `tasks/rtl-rename-recovery-v2/environment/repo`. No model trials or task edits.

## Disposition

**Actual starter matches the approved legacy-migration plan.** No near-complete multi-record or alias/recovery algorithm was found in the reviewed sources. README accurately discloses the legacy subset and permits replacing all helper logic. This closes the starter-scope/fairness review; private oracle/reference validation remains separate and pending. No numerical difficulty endorsement follows.

## Source evidence

- `design.sv` holds one `occupied`/`completed` record and a packed committed map. It fixes lane 1 acceptance to zero and declines branches/moves. Ordinary completion checks both ports by identity and destination. Retirement updates one mapping. No ROB array, branch checkpoint storage, ordered multi-record transition engine or rollback reconstruction is supplied.
- `map_bypass.sv` performs only committed-map lane-0 lookups. It does not contain speculative-history replay or intra-bundle alias/bypass handling.
- `ownership.sv` builds a reserved set from committed tags plus the one pending destination, selecting a single tag. This is useful basic allocation scaffolding, but does not implement dual admission, alias producer readiness or multi-record recovery.
- README openly calls the task a feature migration and lists absent behavior. It permits reconstruction/reference counts and different legal allocators. It does not expose the prior blind patch, private oracle, desired pass ratio or private scoreboard.
- The public smoke exercises the ordinary single-instruction path, sparse port-1 completion, held retirement and later committed-source lookup. It does not contain the missing feature algorithm.

## Independently executed check

Compiled the actual starter plus public smoke with local `iverilog -g2012 -s smoke` into `work/rename-v2-expert-review/legacy-smoke` and ran `vvp`. Result: **PUBLIC_LEGACY_SMOKE_PASSED**, exit 0. This verifies the advertised limited demonstration, not the full v2 contract or pinned-container synthesis acceptance.

## Actual residual work — LLM judgment

The solver must create bounded multi-record storage and next-state processing, speculative and lane-bypassed mappings, alias-aware readiness, dual-resource allocation, retirement compaction and branch-relative recovery. Restoring three predicates cannot create absent state. Shared tags further separate instruction completion, physical production and mapping ownership.

A clean full rewrite remains the easiest plausible solution. The public contract deliberately specifies ownership and edge ordering; the solver need not invent a full out-of-order core, circular ROB, reference counter or physical checkpoint implementation. This starter materially increases residual work over v1 but is not evidence that Astra will fail four of five attempts. Preserve that caveat through the one frozen five-run batch and pause.

## Remaining handoff

Await the separately validated alias-aware private oracle/reference, meaningful starter failure, semantic negatives and accepted alternative implementations. Carry forward sparse completion, invalid-output-X and infrastructure classification regressions. Existing frozen v1 assets and all model outcomes remain unchanged.

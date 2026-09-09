# V2 validation handoff

The new task is `rtl-rename-recovery-v2`: an original single-inflight legacy controller migration to full two-wide speculative rename with move elimination/shared physical tags. Scope is move-alias-only; no operand-read leases. Target remains one observed pass in five total fresh attempts, then pause. No model trial has been run by the author, and difficulty remains unmeasured. Root owns freeze and the bounded batch.

The independent reviewer closed the draft-4 contract and actual-starter scope. The starter has one pending ordinary record and no supplied ROB/recovery/alias engine; its public smoke passed both independently under native Icarus and inside the pinned candidate image as node. Compact reconstruction and complete rewrites remain accepted.

Author matrix is recorded under `work/rename-v2-validation/`, with `summary.json` and per-case source hashes, synthesis/runtime logs, and directed failure witnesses. Four intended positives are ascending reconstruction, descending allocation, invalid-lane X output, and registered physical readiness with recomputed per-tag reference counts. Negative controls must synthesize and fail deterministic directed observations, not merely crash compilation. The task's `validation.json` will carry the completed matrix and exact final assets.

Independent direct HDL evidence at `work/rename-v2-expert-review/alias-witness.json` does not use the Ledger/Campaign: after an early move acknowledgement the ordinary producer remains unready, and an incomplete move to a ready value stays ready. Oracle observations are [0,1]; the alias-done readiness fault gives [1,0]. Full review is in `docs/rename-v2-implementation-review.md`.

Bounded integrity controls passed on image `sha256:567770e7c43368c550dea47ef88b14ae94f247801656dce824777c85111c9a72`: blackbox and reward-write attempts fail synthesis; forged success text fails functionality; missing tools produce infrastructure status with no reward; uid1000 and uid65534 cannot read/write root-only reward storage. These checks are not a general security audit. The executable grader remains byte-identical to reviewed V1 except that its imported protocol/reference/schedules now implement move semantics; binary observation encoding and sparse completion-port tests are retained.

Author debug caught an omitted move-kind record bit before pinned validation: early alias acknowledgement incorrectly woke the physical producer. The corrected record stores `dispatch_move[ni]`; before/after native logs are retained under `work/rename-v2/`. This is an author implementation defect, not a model outcome.

Prior-task preservation check compared 52 pre-existing task-file hashes with zero changes. Prior blind evidence and all frozen tasks remain intact. Harbor oracle preflight, final review closure and current-hash reconciliation are separate root gates before freeze. No PPA, exhaustive verification or numerical difficulty claim is made.

## Completed author matrix

All four positive implementations passed synthesis and behavior for all six configurations. The compiling starter plus twenty semantic faults each failed a directed functional witness. All eight alias-specific faults were detected, including unnecessary free-register gating in PHYS16/ROB16, self-move stale reclamation and killed-alias reclamation. No executable asset changes were required during the pinned matrix. Exact sources, coverage and classifications are in `tasks/rtl-rename-recovery-v2/validation.json`. Independent final closure and root Harbor hash reconciliation remain pending.

Independent final review CLOSED after checking all 18 asset hashes, four six-configuration positive results, twenty-one directed negative results and bounded isolation evidence. No executable changes or broad rerun were requested. Root Harbor reconciliation/freeze remains a separate integration responsibility.

# V2 plan review: fairness passes, difficulty case remains weak

Date: 2026-09-09. Advisory independent LLM judgment. Reviewed `rename-recovery-v2-contract.md` and `rename-recovery-v2-design.md`; actual new starter is not implemented yet. Batch cap: **one frozen five-run batch, then pause**. Requested outcome is 1/5 observed pass, not a probability guarantee.

## Decision

The proposed legacy-to-speculative migration is fair and materially larger than the previous three-predicate repair. It passes a plan-level realism/fairness review. **I do not endorse starter replacement alone as a strong response to the user's aggressive difficulty request.** Recommend one coherent semantic extension before implementation if the root authorizes the additional contract/grader work. If the root retains the legacy-only scope, record the residual ease risk and proceed honestly rather than claiming it is sufficiently hard.

This is not approval of an absent starter, oracle package or final grader. No task implementation or model trial was performed in this review.

## Concrete evidence and easiest valid solution

A local comparison found the v2 normative behavioral section identical to v1 after trimming trailing whitespace. The existing complete oracle is **193 source lines** across three files (130/34/29, including interface/comments). Line count does not measure difficulty, but this executable constructive witness establishes that a full solution need not be a large implementation. The old oracle is private and must not be supplied to candidates.

The easiest legitimate architecture remains:

1. Store a bounded ordered array of records plus committed mappings.
2. Fold the live records to reconstruct speculative mappings, physical ownership and readiness.
3. Count free tags, ROB slots and unresolved branches to admit the maximal dispatch prefix; fold lane 0 into lane 1 lookup.
4. Offer the completed/resolved head prefix for retirement.
5. Build the next array by committing/removing the head prefix, truncating at recovery, matching surviving completions, then appending dispatch.

No physically stored map checkpoint, explicit free-list recovery algorithm, circular-buffer wrap comparison, allocation-generation protocol, execution data path or multi-cycle recovery controller is necessary. The contract explicitly permits reconstruction, and those alternatives must stay legal. This is a conventional bounded state-machine implementation plausibly of the same order of size as the existing 193-line oracle; no reliable solve-time estimate follows.

## What the solver must actually do

| Already mechanically specified | Genuine remaining engineering |
|---|---|
| Owned-set equation and live-record map fold | Choose packed arrays/records and synthesize dynamic selection safely |
| Exact resource admission and lane ordering | Connect allocation, source bypass and resource consumption without combinational mistakes |
| Ordered edge-phase table and recovery boundary | Integrate compaction, older commits and completion matching in one consistent next-state calculation |
| Transport token lifetime supplied by environment | Search surviving records and ignore old identities correctly |
| Finite parameters and reset map | Generalize widths, loops and source metadata across six configurations |

The proposed starter no longer performs that integration, so a local three-condition fix is impossible if the implementation follows the plan. However, the architectural invention burden remains low: the contract supplies a near-executable mathematical design. Missing code is more work than broken predicates, but does not demonstrate that a capable code-generation model will fail most attempts. The remaining easiest path is a clean complete rewrite; it is not an exploit to prohibit.

## Recommended bounded extension: move elimination and shared physical tags

A realistic extension is register-move elimination: selected rename operations alias an existing source physical tag instead of allocating a new tag. This changes a central simplifying invariant rather than adding unrelated protocol puzzles. It couples admission, lane bypass, readiness, ownership, retirement and rollback.

**Engineering depth:** multiple architectural mappings and live moves can share a tag; a move behind an incomplete producer inherits that producer's readiness; a lane-1 move can alias a lane-0 allocation; retirement/rollback must not free a tag still referenced by another surviving mapping. An alias move can be accepted with no free physical tags when ROB/checkpoint resources permit. A move's own completion must not incorrectly wake the underlying producer. These require changing the ownership/readiness model, not merely enlarging the current queue.

**Contract costs before approval:** add an explicit move-kind input and specify its legal combinations with branch/write enable; select the aliased source; define zero-register/source behavior; define renamed destination/stale metadata and resource cost; separate producer readiness from instruction completion; specify when a move becomes retirement-eligible; define same-edge producer completion, aliasing and recovery; state physical reuse safety with late events. Replace the current prohibition on shared live/committed destination tags. Keep all alternative correct representations legal, including set/reconstruction approaches.

**Grader costs:** the existing unique-destination assertions and readiness assignment per record become invalid. Build an independent alias/dependency history model with physical-producer provenance, not a shallow patch of the oracle. Require directed schedules for two aliases of one producer, overwrite/retire of one alias, pending-source moves, lane-0 producer/lane-1 alias, recovery retaining one alias while killing another, zero-source aliases, and full-physical-capacity alias admission. Controls must reject premature tag reclamation, allocating for every move, false readiness from move completion, and lost same-bundle aliasing. Validate a passing original oracle and a different correct bookkeeping strategy before freeze.

This extension is a recommendation to the root, not authorization for the author to change scope. It raises authoring/verification cost and risk, and still cannot promise 1/5 pass. Do not combine it with exceptions, vector renaming or PPA constraints merely to accumulate complexity.

## Fairness and independence conditions

Publicly state the legacy subset and missing feature work. Keep smoke tests illustrative; do not embed the completed architecture in helper code, comments or reference traces. Reusing private v1 tests/oracle is sound only for unchanged semantics. For the proposed alias extension, reusing infrastructure is sensible but behavioral reference/oracle agreement must be independently re-established. Preserve sparse-completion, bit-preserving unknown-output, signal/infrastructure and alternative-allocation controls.

No hidden semantics, solver-history leakage, mandated internal microarchitecture, arbitrary timeout tightening or numerical hardness multiplier is acceptable. The old successful result remains valid. Freeze the selected package before all five fresh attempts and keep every outcome; no redesign during that batch.

## Handoff

Sent root and author the fairness-versus-difficulty distinction and bounded extension recommendation. Await root's scope decision before the author implements. If legacy-only v2 is chosen, require actual-starter inspection and oracle/grader validation, but label difficulty as unmeasured with a plausible compact-solution risk.

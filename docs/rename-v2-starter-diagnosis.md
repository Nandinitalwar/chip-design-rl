# Rename v2: diagnosis of prior starter and review criteria

Date: 2026-09-09. Independent LLM judge. Target for the next frozen batch: **1 pass in 5 valid fresh attempts**. This is a requested observed ratio, not a guaranteed population rate. No v2 model trials or task edits were performed by this reviewer.

## Observed evidence

`docs/blind-attempt.patch` contains three functional repairs, plus comments:

| Location | Supplied defect | Submitted repair |
|---|---|---|
| Completion lookup | Physical-tag match with identity replaced by constant true | Restore live instruction-token equality |
| Intra-bundle map update | Apply only for lane 1 | Apply for every accepted effective writer |
| Owned-set construction | Include only completed live destinations | Include every live destination regardless of completion |

`docs/blind-attempt.json` records one fresh Astra/high desktop-harness attempt, 288.415 seconds, reward 1 on all six synthesis/functional configurations. The attempt had public instruction/starter context; host-tool isolation was instructed rather than technically removed. Preserve that harness qualification and do not pool with the earlier Harbor results. A single pass does not establish the underlying pass rate.

## Diagnosis — LLM judgment

The previous review correctly identified substantial *contract* interactions but overstated how much engineering the *starter* left to the solver. Its packed-record ROB, committed-map updates, retirement compaction, recovery-prefix selection, surviving-completion phase, map replay, resource counting, checkpoint accounting and maximal-prefix admission were already implemented. Their ordering largely mirrored the specification. Each altered predicate was a visible deviation from an otherwise working architecture.

All three defects were local, with direct contract clues and no need to change state representation or module interfaces. The completion predicate even contained an obvious constant-true placeholder. Supplying the central reconstruction algorithm removed the difficult ownership/recovery design decision. A three-module layout did not create three independently challenging integration tasks. Broad private coverage made the reward more trustworthy but did not add work to the repair.

The evidence supports revising the intended difficulty mechanism. It does not support a numerical forecast that Astra will pass every future attempt, nor does it show reward exploitation. The submitted solution repaired the intended semantics.

## Gate for the author's v2 plan

Review the actual public starter alongside its proposed contract before implementation. Require a concise inventory separating already-correct infrastructure from new behavior that must be designed. Identify the maintained invariants, stored information and interface/event changes that a correct solution needs. Explain why the smallest legal patch is substantively more than toggling known conditions. Changed-line count and file count alone are insufficient.

A coherent feature migration can provide real depth: existing behavior remains useful while new semantics require a maintained invariant across acceptance, completion, ownership and recovery. The feature must have a concrete engineering purpose. Merely adding inverted conditions, arbitrary event priorities, very large arrays, tighter runtime limits or obscure encodings would create artificial difficulty and will not receive approval on that basis.

The contract must disclose all observable timing, legal-input assumptions, cancellation/identity lifetime, resource admission, reset and backpressure behavior. A simpler reconstruction-based implementation remains legitimate when it satisfies the published behavior and tool/resource limits. Do not impose a secret internal data structure, forbid an otherwise correct approach after observing it, or count a specification ambiguity as a model failure.

The private reference must derive behavior from transaction history or another separately justified model, not translate the candidate oracle line-for-line. Carry forward the sparse-port, invalid-output-X and runtime-infrastructure controls. Add feature-specific negative controls and at least one substantively different valid strategy where practical. Demonstrate that the intended new behavior is observed, and that ordinary alternative timing/allocations remain accepted wherever the contract allows them.

## Batch discipline

The root will freeze one reviewed revision for all five fresh attempts, retain every outcome and adjudicate infrastructure separately. Each solver receives only the authorized public task and generic execution adapter; prior patch/reviews/oracle/private tests/desired success count must not enter its context. Redesign only between batches. Stop at the authorized batch boundary, not when the preferred count happens to appear. Further redesigns and runs remain subject to the root's authorized scope/budget.

## Handoff

Diagnosis sent directly to the author. Await v2 contract and starter plan; this document does not approve an absent design, implement v2, freeze assets or authorize trials. Preserve the existing frozen task and its successful outcome.

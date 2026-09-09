# Hard-task proposal review by independent LLM judge

Date: 2026-09-09. Input: [research handoff](hard-task-research.md), eight proposals. Authoritative target: **20% PASS / 80% failure on gpt-6-astra/high**. All candidates are unimplemented and uncalibrated. This document is advisory **LLM engineering judgment**, not a deterministic result, human expert certification or estimated pass probability. No tasks were changed and no trials were run.

## Decision

Select **R1 rename/recovery**, **R2 speculative LSU**, and **R3 selective TLB invalidation** for specification refinement, in that order. Author R1 first once its contract is closed; do not implement all three simultaneously merely to increase volume. R1 offers the best balance of genuine interacting state and a tractable external reference. R2 has comparable depth but greater oracle risk. R3 is a bounded third candidate with a particularly important missing-information problem at fence time.

CPU simulation is demonstrated in this repository. Trainium2 availability is not established by the reviewed evidence, and synthesis validation remains an open project requirement. Thus “CPU feasible” below means plausible implementation/validation on the existing platform, not already validated. K1 is the strongest accelerator reserve if hardware and compiler preflight become available.

## Comparative ranking — LLM judgments only

Scores: 1 weak, 5 strong. Grading and shortcut scores assess the proposals after the identified contract repairs, not existing implementations. Hardware readiness is assessed separately rather than hidden in a total score.

| Rank | Candidate | Realism | Interacting mechanisms | Fair deterministic grading | Shortcut resistance | Hardware readiness | Likely ease for Astra: hypothesis only |
|---|---|---:|---:|---:|---:|---|---|
| 1 | R1 rename/free-list/retirement recovery | 5 | 5 | 4 | 4 | CPU feasible | Less likely to collapse to one local fix; familiar rename algorithms may still make it easier than hoped |
| 2 | R2 speculative LSU/byte forwarding | 5 | 5 | 4 | 4 | CPU feasible | Temporal and byte-level dependencies may challenge integration; a clean small-queue algorithm may still solve it readily |
| 3 | R3 selective TLB/in-flight walks | 5 | 4 | 4 | 4 | CPU feasible | Medium ease risk after precise semantics; a correct fence-history design is compact |
| 4 | R4 cache refill/merge/invalidation | 4 | 5 | 3 | 4 | CPU feasible, substantial verifier work | Potentially hard, but ambiguity and oracle defects could dominate model difficulty |
| 5 | K1 paged grouped-query attention | 5 | 5 | 4 | 3 | Trainium2 unverified | Known attention algorithms lower novelty; unfamiliar layout/compiler constraints may dominate failures |
| 6 | R5 fence.i drain/fetch recovery | 5 | 3 | 5 | 3 | CPU feasible | Highest ease risk among RTL choices: small state machine plus response identity tracking |
| 7 | K2 dropless MoE | 5 | 4 | 4 | 3 | Trainium2 unverified | Correct gather-based combine may avoid the apparent scatter challenge |
| 8 | K3 RMSNorm/projection | 4 | 3 | 4 | 2 | Trainium2 unverified | Straightforward slow multi-pass strategy may satisfy correctness; optimization difficulty needs measured constraints |

R4 moves above K1 for current local feasibility; R5 moves above K2 for inexpensive fair grading. Neither change claims a measured model ranking. Do not interpret scores as evidence for 20% pass.

## Evidence checked versus proposed behavior

The research document contains the full source trail. I checked three primary sources supporting the selected mechanisms:

- BOOM describes superscalar rename bypass, stale-destination reclamation at commit and a snapshot-related free-list leak. This supports R1's realism; the proposed two-lane interface and edge priorities are ours. [BOOM rename stage](https://docs.boom-core.org/en/latest/sections/rename-stage.html).
- BOOM describes separately available store addresses/data, forwarding, sleeping loads and ordering-failure recovery. R2's byte-mask rules and earliest replay policy must be specified as this task's contract, not asserted to reproduce BOOM exactly. [BOOM LSU](https://docs.boom-core.org/en/latest/sections/load-store-unit.html).
- The versioned RISC-V supervisor specification permits over-fencing and prohibits stale speculative fills across a subsuming fence. Retaining unrelated translations is therefore an additional product requirement. [RISC-V Supervisor ISA v20260120](https://docs.riscv.org/reference/isa/v20260120/priv/supervisor.html).

These sources establish mechanisms, not candidate correctness or difficulty. The Rocket issue cited by the researcher remains unreplicated reporter evidence and is unnecessary to establish the selected R3 contract. Accelerator and other reserve candidates were assessed from the supplied briefs; their linked sources were not independently re-audited in this review.

## R1 — selected first: close ownership and event semantics

**Smallest complete scope.** Two rename lanes, eight architectural registers, bounded retirement records, four branch checkpoints and the proposed physical-register configurations. Keep execution outside the task: trusted completion events carry instruction identity and physical destination. Grade tag mapping/readiness and retirement ownership, not arithmetic execution. If committed-value checking is retained, supply a trusted value adapter with an explicit contract. Branches should initially have no destination, with at most one branch per accepted bundle; same-bundle dependencies and nested branches remain.

**Required contract changes.** Publish a per-edge table: reset dominates; validated in-order older commits apply; recovery kills strictly younger records; surviving completions update readiness; dispatch is disabled on recovery. Specify simultaneous commit count, completion count and correctly predicted branch release. Resolve the boundary between lanes: a lane-0 branch checkpoint includes older state and that branch, excludes lane 1; a lane-1 branch includes lane 0. State whether a lane-0 destination may forward to lane 1 and whether source lookup precedes its own destination update. Define zero-register behavior and no-destination instructions.

Allow any legal physical allocation order. Define the public acceptance rule, including partial bundle acceptance and whether same-edge freed registers are allocatable. A simple initial choice is ordered-prefix acceptance using pre-edge free capacity; full two-lane acceptance is required when all named resources and downstream capacity are available. State a finite recovery completion bound supported by the oracle, rather than demanding an arbitrary cycle count after seeing model outputs.

Finite generation counters alone do not guarantee safety with indefinitely delayed completions. Require outstanding-identity tracking with no reuse until its old response is consumed, or an explicit transport cancellation acknowledgement. Specify eventual response/ack fairness; otherwise finite-resource liveness is impossible. No hidden epoch-wrap assumption.

**Independent grader.** Use an instruction-history ledger and candidate-emitted tags. Derive speculative mappings from surviving instruction history; derive liveness from mappings, in-flight destinations, still-needed operands and retirement dependencies. Do not equate “absent from current map” with “free.” Compare source tags and readiness; check allocation uniqueness, exact retirement order and recovered capacity. Avoid translating the oracle's checkpoint bitsets into the reference.

**Decisive schedules/controls.** Same-register writes in both lanes; checkpoint between lanes; older commit frees a tag that younger work reuses before rollback; nested checkpoint resolution and reuse; delayed killed completion after physical reuse; output backpressure during recovery. Negative controls: snapshot-only free-list restoration, lost commit reclamation, missing lane bypass, wrong checkpoint boundary, stale completion readiness and permanent single-lane dispatch. Include at least two valid allocators with different priorities to prove the grader tolerates legal choices.

## R2 — selected second: make speculation observable and replay unambiguous

**Smallest complete scope.** Single-hart aligned 64-bit words, byte enables, eight load/store slots, externally supplied instruction ages and split store address/data events. Exclude atomics, MMIO, cross-word accesses, coherence probes and full RVWMO conformance. Provide trusted memory and retirement adapters; those adapters must not silently repair a candidate's stale load.

**Required contract changes.** For each requested byte, select the youngest older matching store. If its data is unavailable, that byte blocks completion; it must not fall back to memory or an older store. Bytes not requested are unconstrained. Specify whether memory can be requested for remaining bytes before all forwarding resolves and the memory read's linearization point. Define how forwarding survives store-queue removal until committed stores are visible in backing memory.

Define replay using externally observable events, not an undefined internal “executed” bit. One fair initial policy: when an older store address resolves, select the oldest younger load whose speculative completion was accepted and whose requested bytes overlap; conservatively replay even if the numerical value would be unchanged. This is a declared product policy. Pending, not-yet-completed loads must revalidate before completing. The replayed load is killed inclusively along with younger work. Specify that same-edge conflict/recovery suppresses completion/retirement for killed identities; hold replay notification under backpressure while cancellation takes effect at the defined detection edge.

Publish instruction-age wrap rules, outstanding request identity lifetime, response acceptance and squash acknowledgment. Require independent-load issue within a declared bound only when queue capacity, request-ready and arbitration assumptions hold. Require at least one specified speculative-issue case while an older address remains unknown. Do not use unqualified “eventually” or let the grader choose deadlines after seeing implementations.

**Independent grader.** Sequential committed byte-array comparison plus a separate issue/completion/replay ledger. The architectural model must execute original program order, not accept candidate replay decisions as ground truth. The event ledger independently identifies overlap and age, records response ownership and detects missing/duplicate completions. Both are needed: architectural checking alone rewards full serialization; replay-only checking can miss stale retirement.

**Decisive schedules/controls.** Two older stores supplying different and overlapping bytes, youngest data delayed, unrelated younger load, unresolved alias resolved with a same-edge memory response, out-of-order responses across queue wrap, committed store awaiting visibility, and replay output stalled. Controls: oldest-match forwarding, whole-word forwarding, fallback through unavailable data, missed replay, stale response slot reuse, and serialized loads. Validate a correct alternative strategy with conservative extra memory requests where the public contract permits them.

## R3 — selected third, conditional on resolving fence-time information

**Smallest complete scope.** Translation cache with trusted walk responses, two clients, eight entries, four outstanding requests, 4 KiB/2 MiB ranges and ASID/global tags. Exclude page-table parsing, permissions computation, nested translation and unsupported virtual addresses; define these input assumptions explicitly.

**Critical gap in the brief.** Page size and global status may arrive only with the response. A selected-address fence inside a future superpage can subsume a walk requested at a different 4 KiB address. At fence time the candidate cannot necessarily decide exact cancellation from the request VPN/ASID. Do not grade it as if that metadata were already known.

For the first version, permit conservative cancellation of potentially matching outstanding walks while requiring exact selectivity for already-resident entries. Alternatively expose sufficient trusted metadata at walk acceptance, or specify bounded fence-history retention until response metadata permits matching. Exact retention of unknown future translations should not become a hidden obligation. Define safe behavior when history capacity is full, with permitted backpressure and a fairness assumption; never rely on a generation counter not wrapping.

Publish independent all-address/all-ASID flags so address zero and ASID zero remain selectable values. Specify global-entry matching, superpage interior matching, simultaneous fence/fill/lookup ordering, cancellation/retry notification and held client responses. Define fence completion in terms of preventing future stale deliveries as well as fills. Resident selectivity tests should avoid unrelated replacement pressure, or state a replacement policy; otherwise a legitimate eviction could be falsely labeled over-fencing. Define duplicate/overlapping-fill handling or restrict the legal environment to avoid ambiguous hits.

**Independent grader.** Interval/ASID reference with fence history and externally tracked request lifetimes. Test two different 4 KiB requests later returning the same superpage; targeted fence inside that range; global response after ASID-selective fence; simultaneous I/D activity; multiple fences before response; identity reuse pressure; response backpressure across a fence. Controls: resident-only invalidation, exact-VPN matching, treating ASID zero as all-ASID, global-entry misclassification, stale-response reuse, and global flush of unrelated resident entries. Accept conservative outstanding-walk cancellation if the selected contract allows it.

## Reserve decisions and rejected artificial difficulty

- **R4:** retain for later. Its custom coherence-like protocol needs a complete linearization table, dirty-byte responsibility and error-response semantics before oracle development. Larger size is not evidence of productive difficulty.
- **K1:** first hardware reserve. Close absolute-position/window/all-masked conventions, cast boundaries and error tolerances; validate hardware compilation and memory accounting before imposing a latency/workspace limit. Accept alternative correct reduction strategies. Do not require split reduction internally unless it is an observable, justified engineering constraint.
- **R5:** useful lower-difficulty control. Do not add arbitrary handshake phases to force failures.
- **K2:** retain, but accept conflict-free gather; scatter atomics are not intrinsically the task goal. A full original kernel plus runtime constraints requires hardware validation.
- **K3:** defer until a realistic resource/performance requirement has evidence. Reject invented timing cutoffs, prohibited-but-unobservable intermediates, or extra quantization solely to reduce pass rate.

For all candidates, reject hidden semantics, grader dependence on a particular allocation/layout, artificially tiny time budgets and source-copy trivia. Familiar algorithms remain legitimate solutions. Provide original realistic bug scaffolding and a smoke test without leaking the private oracle. Preserve difficulty through genuine concurrency and externally visible requirements.

## Gates before model calibration

Freeze complete contracts first. Independently derive a reference and validate a passing oracle, a meaningfully failing starter, targeted controls and valid alternative implementations. Include reduced exhaustive event schedules and fixed-seed stress. Enforce synthesizability and protect reward computation outside candidate-writable state; a simulator success string alone is insufficient. Separate tooling faults from candidate failures. No current task edits are requested by these recommendations.

Only then authorize a distinct fixed-version campaign with recorded settings. Target is 20% pass; no selected candidate has evidence of that rate. Report all outcomes and intervals (2/10 passes is only a noisy screen), and reserve independent validation after revisions. Never keep tuning until exactly two successes appear.

## Handoff

Selected R1/R2/R3 for contract refinement; R1 recommended for first authoring after the above decisions. This review creates no implementation or campaign. Frozen existing tasks and trial artifacts remain unchanged.

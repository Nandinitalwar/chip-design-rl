# V2 move-alias contract review

Date: 2026-09-09. Reviewed move-only contract draft 2 and starter plan. Advisory LLM reasoning, no RTL execution or model trials. Existing frozen tasks/results unchanged. Exactly one five-run batch remains the cap; no numerical difficulty prediction.

## Disposition

The move-only contract is coherent and fair in its bounded execution-adapter scope, pending the wording fixes below and root's final scope reconciliation. No additional feature is needed for this review's move-only approval. A precise operand-read-lease proposal is not present in the reviewed draft; no approval or technical rejection of unseen lease semantics is implied.

The actual starter must still be inspected after authoring. Oracle, alias-aware reference and semantic controls must be validated before freeze.

## Why this changes the residual engineering problem

Legacy migration removes preimplemented multi-record transitions. Aliasing additionally changes a core state invariant: effective mapping writes no longer imply new physical allocation, and instruction completion no longer always determines destination readiness. Multiple committed/live owners can share one physical value. A solver must integrate distinct allocation, mapping, ownership and readiness decisions across dual dispatch, source overwrite, retirement and recovery.

This is materially different from v1's three predicate repairs. However, a small ordered-record reconstruction solution remains legal and plausible. Correctness can be achieved with committed mappings, records marked ordinary/move, and readiness derived from actual allocating producers. The feature does not guarantee a low pass rate or a need for complex reference counters.

## Accepted contract reasoning

- Moves capture their source-A physical tag before their own update, with intra-bundle forwarding. Subsequent architectural source overwrite cannot change that captured identity.
- The move's bookkeeping acknowledgement controls its record completion, not the physical producer's readiness. Source-ready aliases stay ready despite an incomplete move; early move completion cannot wake an older incomplete producer.
- Owned-set union over committed tags and live effective destinations admits aliases while retaining tags referenced by any survivor. Unconditional stale freeing is invalid, especially for self-moves or multiple committed aliases.
- A nonzero destination can alias p0; a destination-zero move changes no mapping, outputs zero destination/stale, but retains its move metadata. Ordinary allocation must never allocate p0.
- Prefix admission charges physical capacity only for ordinary effective writers. Same-edge resources and completion readiness remain unavailable until the following cycle; source lookup follows the existing lane order.
- Producer lifetime is coherent under in-order retirement and suffix recovery. An unready captured producer is older than its surviving aliases. If the producer is removed by retirement, its physical value is already ready; if it is killed, all younger dependent aliases are killed too. Token reservation prevents late killed completions from matching a newly accepted identity.
- Requiring underlying readiness for move retirement is safe, although in-order retirement of earlier producers often makes that predicate redundant. Redundancy should not be advertised as another independent hard mechanism.

## Requested wording fixes

1. Qualify “recovery may free a killed instruction's physical destination immediately”: this is permitted only when the tag has no surviving committed/live owner. A killed move does not independently own a new allocation.
2. State that inherited ordinary-write traces assume no additional aliases, or make every stated free/reclaim conditional on the owned set.
3. Add move kind to the described live-record metadata so `retire_move` and producer-readiness handling are explicit.

These clarify the already-defined owned-set rule; they introduce no new behavior.

## Deterministic validation requirements to implement later

Use directed witnesses for pending-producer/early-move acknowledgement, ready-source/incomplete-move, ordinary lane 0 plus dependent move lane 1, alias chains, source overwrite, self/zero moves, partial retirement of shared aliases, rollback retaining one owner while killing others, and late killed move/ordinary completions after physical reuse. Reference readiness must track producer provenance, not overwrite each tag's readiness with the last alias record's done bit.

For no-free-physical admission, use a reachable case such as **PHYS=16/ROB=16**: eight unique committed tags plus eight live fresh ordinary destinations exhaust PHYS while leaving eight ROB slots. PHYS=24/ROB=16 cannot exhaust physical capacity with a spare ROB slot under the maximum eight committed tags; PHYS=32 with ROB<=16 cannot exhaust physical capacity at all. Tests must not fabricate impossible owned sets or insist on the same saturation witness in every configuration.

Retain ordinary and descending allocators, a valid invalid-output-X implementation, sparse completion placements and infrastructure classification controls. For alias semantics, aim for a second valid implementation with different ownership/readiness bookkeeping; allocator reversal alone exercises allocation freedom, not independence of the new semantic model.

## Handoff

Findings sent to author and root. Root has been told the current draft excludes leases; a lease extension would require a concrete public transport contract before any review. Recommend closing at the coherent move-only scope and proceeding to authoring once wording and scope are settled, without further feature escalation.

## Draft-4 closure — final move-only scope

Reviewed active contract draft 4. It explicitly excludes leases and extra reader lifecycles, qualifies killed-tag reclamation by surviving ownership, limits inherited free-tag examples to no-extra-alias cases, and includes move kind in live-record metadata. The reachable PHYS=16/ROB=16 admission witness is recorded. Existing identity, alias-ready, source-overwrite, lane-prefix and event-order semantics remain coherent.

**Material contract questions are closed; author may implement under the root's existing assignment.** Scope is closed at legacy migration plus move elimination/shared tags. This is contract approval, not implementation or grader approval. The actual starter must still be checked to ensure it withholds multi-record/alias/recovery algorithms, and alias-aware oracle/reference/alternative-control evidence must pass before freeze. A compact valid reconstruction remains possible; no difficulty guarantee follows. Exactly one five-run batch, then pause.

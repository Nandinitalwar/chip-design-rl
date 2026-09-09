# R1 contract review — independent LLM judge

Date: 2026-09-09. Reviewed `rename-recovery-contract.md`, contract-draft-1. Target remains 20% pass / 80% failure, uncalibrated. This is source-level LLM reasoning only; no RTL, synthesis, simulation or model trials were run.

## Disposition

Contract is substantively coherent, pending two explicit interface clarifications sent to the author. No changes to existing tasks or trial results are requested.

1. **Material: retirement lane compaction versus stability.** With valid=11 and ready=01, oldest A transfers, while B must move from lane 1 to lane 0 next cycle. The blanket statement that valid identities/fields stay stable under backpressure can be read to forbid this required shift. Specify stability per record, recompute lane positions from the current head, and require same-lane stability only when no earlier record transfers. B's metadata remains unchanged; its lane need not remain unchanged. New C may become the second offer.
2. **Interface completeness: no-destination retirement fields.** Explicitly define `retire_dst_we` as effective write enable (`dispatch_dst_we && dispatch_dst != 0`); `retire_arch_dst` as the original dispatch destination; `retire_branch` as original branch flag; and destination/stale physical tags as zero when there is no effective destination. An alternative is to mark unused fields unconstrained, but the grader must follow that choice. The draft currently makes all valid retirement fields meaningful without spelling out this mapping.

Editorial correction: the worked commit/reuse/recover trace may have a second commit older than B but younger than already-retired W. A record older than W cannot commit after W under the in-order contract.

## Accepted reasoning

- Committed-map tags union live effective destinations is sufficient ownership for this scope. A younger writer cannot retire and reclaim an older reader's needed mapping before that reader retires. Killing a suffix cannot leave a surviving earlier reader dependent on a killed younger destination. This relies on program-order retirement and absence of move-elimination/tag aliasing, both consistent with the contract.
- Stale mappings are computed before each lane's own update, with lane-0 bypass to lane 1. At in-order retirement, each effective writer's stored stale tag is the mapping displaced from the committed map. Different legal allocation priorities remain admissible.
- A checkpoint immediately after a destination-free branch unambiguously includes lane 0 when the branch is in lane 1, and excludes lane 1 when the branch is in lane 0. Reconstructing from committed mappings and the surviving ordered prefix correctly incorporates same-edge older commits.
- External identity reservations survive killed-record removal until completion consumption. This permits immediate physical reuse without ambiguous old completions, provided live instruction identity is checked. No bounded generation-counter assumption is needed. Reset transport cancellation is explicit.
- Pre-edge resource admission and no same-edge completion/retirement bypass give deterministic timing. One-edge reconstruction is functionally plausible for bounded arrays; this is not measured synthesis, timing or area evidence.
- Separate branch completion and resolution is a meaningful bounded control interaction. The branch remains retirement-blocking until both occur; invalid/killed resolutions are excluded by the environment contract. It does not require an execution model.

## Validation additions for author

Retain both valid allocation strategies and the planned mutation suite. Add a directed retirement compaction witness (A/B valid, accept A only, confirm B unchanged at lane 0), effective-zero-destination metadata checks, both completion-before-resolution and resolution-before-completion branches, a surviving completion on the recovery edge, and killed-token/physical-reuse collisions across token wrap. These are deterministic grader witnesses to implement later, not tests run by this review.

Await draft-2 for closure before implementation.

## Draft-2 closure

Reviewed contract-draft-2 after the author's handoff. The retirement section now explicitly permits lane compaction while preserving per-record metadata, defines effective write enable and canonical no-destination retirement fields, and corrects the worked trace's age ordering. **The material contract ambiguities raised in this review are closed.** R1 may proceed to implementation under the orchestrator's existing assignment. This is approval of the behavioral contract for authoring, not approval of future RTL, synthesis, grader integrity, release readiness or measured difficulty. Retain the validation additions above.

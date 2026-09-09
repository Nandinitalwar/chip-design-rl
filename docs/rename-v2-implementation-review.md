# V2 alias implementation and grader review

Date: 2026-09-09. Independent LLM judge. No model trials or task edits. Target remains one observed pass in one five-run batch, followed by pause; difficulty is unmeasured.

## Current disposition — final review closed

Final author evidence and all 18 current asset hashes have been checked. **Independent judge review is closed for root integration/freeze consideration.** No definite material contract, starter or grader defect remains from this review. Root retains Harbor reconciliation and the single five-attempt batch. This is not a measured-difficulty, PPA or general security certification.

## Preliminary disposition (historical)

Preliminary source review found no definite contract/implementation disagreement in the inspected alias paths. An independent native HDL witness confirms the key separation of move acknowledgement and physical readiness. **Final approval remains pending the author's complete pinned validation and final asset handoff.** This does not replace that matrix or Harbor integration preflight.

## Source inspection — LLM judgments

- Oracle records now store move kind, and retirement exposes it. Admission charges a physical tag only for effective ordinary writers; mapper aliases moves to the source-A tag before the lane's own update and forwards lane 0 into lane 1.
- Ownership unions committed mappings and live effective destination tags. Ready reconstruction initializes committed values as ready and applies completion status only from live ordinary allocating producers. Alias records do not clear or set readiness. This is consistent with in-order retirement and suffix recovery.
- The reference uses persistent physical-value entries carrying producer identity/readiness, distinct from instruction `done`. Ordinary allocation initializes that value entry, surviving ordinary completion marks it ready, and moves update mappings without changing the value. Killed completions are ignored. This is a useful independent representation of the new readiness rule, although the reference and oracle share the same public ownership equation and are not proofs of each other's correctness.
- The positive alternative stores physical readiness in registers while counting current references per physical tag. Those reference counts are recomputed combinationally, not maintained incrementally. Describe it as registered readiness plus recomputed reference counts, rather than implying all bookkeeping is incremental. It also reverses allocation priority.
- Directed schedules cover early move acknowledgement, incomplete ready alias, chains, zero/self moves, source overwrite, recovery and partial commit. The no-free-physical witness is restricted to reachable PHYS=16/ROB=16. New stress moves obey branch/write-enable legality.
- At inspection, `grader.py` was byte-identical to reviewed v1. The protocol changed only to carry move input/output bits, retaining sparse completion placement, bit-preserving observations and infrastructure diagnostics. These inherited controls still need current-package execution evidence.

## Independent deterministic readiness witness

Ran actual oracle RTL and an external variant that incorrectly assigns physical readiness from every alias record's completion flag. The witness uses the trusted port serializer but **does not import or invoke the reference ledger or campaign schedules**. It accepts an ordinary producer and dependent move in one bundle, acknowledges the move first on port 1, then queries an alias consumer. After completing the producer, it accepts a new move to the ready value while withholding that move's acknowledgement and queries the new alias.

| Observation | Contract | Oracle | Incorrect alias-done variant |
|---|---:|---:|---:|
| Source readiness after early move acknowledgement | 0 | 0 | 1 |
| Source readiness through an incomplete move after producer completion | 1 | 1 | 0 |

Native Icarus compilation and simulation completed successfully. Evidence and exact source hashes: `work/rename-v2-expert-review/alias-witness.json`, reproducer `alias_witness.py`, retained source variants and protocol snapshot. This is a focused functional witness at default PHYS=24/ROB=16; it does not establish all-configuration synthesis, general correctness or model difficulty.

## Required final handoff

Await complete four-positive/six-configuration results, meaningful starter rejection, alias-specific and retained negative controls, bounded integrity checks, exact current asset hashes and pinned image identity. Reconcile any source/test changes after this inspection before closure. Preserve the actual-starter fairness finding in `rename-v2-starter-review.md` and the compact-rewrite caveat.

## Final evidence reconciliation

Inspected `tasks/rtl-rename-recovery-v2/validation.json`, `work/rename-v2-validation/summary.json`, and `work/rename-v2-isolation/summary.json`. Verified every one of the 18 listed asset-file SHA256 values against current files with zero mismatches. Current oracle hashes also match both the author matrix and this review's independently executed readiness witness. The reported asset-manifest identity is `6f45cc3f06c99d07f6731572cab932c2911b2546b22db70619b514c46c420f05`; pinned image identity is `sha256:567770e7c43368c550dea47ef88b14ae94f247801656dce824777c85111c9a72`. Review record: `work/rename-v2-expert-review/final-review.json`.

The author matrix records four positive implementations each passing all six configurations: oracle, descending allocator, invalid-lane-X, and registered readiness/recomputed reference counts. The starter plus 20 semantic negatives fail directed functional checks after synthesis. Eight alias controls cover new allocation for moves, clearing alias readiness, alias-done readiness corruption, free-tag requirements for moves, source-zero metadata, dropped move metadata, unconditional stale reclamation and killed-alias reclamation. The required no-free-tag move witness fails the intended mutant at `alias-no-free-dual-moves`.

The bounded isolation report rejects a blackbox, forged marker and reward-write attempt; missing tooling is infrastructure; UID 1000/65534 lack read/write access to the protected reward probe. These are author-executed controls inspected here, not a new independent sandbox audit. Similarly, the full pinned matrix was not duplicated by this reviewer: independent execution consisted of the actual public smoke and direct HDL alias-readiness witness, alongside source/contract review and current-hash reconciliation.

The new starter withholds multi-record and alias/recovery algorithms as approved. Legitimate allocation/readiness alternatives and invalid output bits are accepted by recorded validation. A compact complete reconstruction remains a plausible easy solution for Astra. No numerical pass-rate claim follows; preserve all five fresh outcomes on the root-frozen version and pause after that batch.

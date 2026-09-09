# V2 author notes

This task migrates an original single-inflight ordinary controller to two-wide speculative rename with eliminated moves. Target is one observed pass in five independent trials; difficulty remains unmeasured. The author runs deterministic validation only. Root owns freezing and the single authorized five-trial batch, then pauses regardless of outcome. No leases or further feature extensions are included.

## Scope and provenance

The authoritative construction contract is `docs/rename-recovery-v2-contract.md`, draft 4, closed by independent review. The candidate instruction includes the complete behavioral contract. All task RTL, smoke, reference and schedules are original project work; no third-party implementation source was copied. The private oracle and grading boundary extend this project's V1 assets, preserving binary port encoding and the sparse completion-port witness. The candidate starter is newly written legacy code, not a predicate-mutated oracle. Prior tasks and blind evidence are preserved.

The starter has one pending record, a committed map, and a single free-tag picker. Its working ordinary path accepts lane 0, matches a completion on either port, holds a retirement record and commits it. It supplies no multi-record ROB, speculative replay, checkpoint/recovery, alias readiness or dual allocation engine. Candidates may replace all three files and helper interfaces. Compact reconstruction is legal and remains a plausible solution; neither source size nor subjective difficulty predicts model success.

## Independent checking

The oracle uses an ordered packed-record array with bounded map/ownership reconstruction. Shared tags are owned by the union of committed mappings and live effective destinations; readiness is changed only by ordinary allocating producers, never move acknowledgements. Lane-ordered map lookup also captures each move's immutable aliased tag. Pre-edge resource counting charges physical capacity only to ordinary effective destinations.

The external Python reference instead stores instruction-history objects, token transport reservations and a separate persistent physical-value readiness table. Candidate ordinary allocation is checked against the entire legal free set; move allocation must equal the captured source-A tag. The ledger checks ordered retirement, stale mappings, exact maximal acceptance, per-record conservation and ordinary allocating-producer uniqueness without imposing uniqueness on aliases. Killed transports remain reserved until completion consumption. Input-generation assertions are infrastructure defects, not candidate failures.

Positive controls exercise the oracle, descending allocation, unknown bits on invalid output lanes, and a distinct implementation with incremental physical-ready registers and per-tag reference counts. Semantic controls retain ordinary ordering/identity/resource faults and add fresh allocation for moves, readiness corruption by move completion, unnecessary physical-capacity gating, zero-source metadata errors, lost move retirement metadata, unconditional stale reclamation and killed-alias reclamation. Controls must synthesize and fail a directed functional witness to count as semantic discrimination.

Alias schedules cover a pending lane-0 producer with a dependent lane-1 move, early move acknowledgement, incomplete moves of ready values, source overwrite with multiple aliases, dual moves, self/zero moves, destination-zero metadata, partial retirement, both branch lane boundaries, surviving older commit on recovery, and alias ownership after killed moves. The no-free-register witness with spare ROB slots is restricted to reachable PHYS16/ROB16. Each of six configurations retains the ordinary directed witnesses, 48 reduced event combinations and 1,400 deterministic stress cycles, now including moves. These are bounded tests, not exhaustive state-space verification or formal proof.

## Tool and reward boundary

The Dockerfile pins Yosys 0.23-6, Icarus 11.0-1.1+b1 and Codex 0.153.4 on a digest-pinned Node image. Only `environment/repo` is copied into the candidate image. The configured candidate is `node`; the verifier is root, while synthesis and simulation run as uid/gid 65534. Private reference code remains in the privileged controller, only synthesis-generated netlists execute, and reward storage is mode 0700. Binary serialization preserves valid bits adjacent to invalid X outputs. Missing tools and abnormal runtime infrastructure are separated from candidate synthesis/functional failures. Bounded forgery, reward-write, blackbox, missing-tool and permission controls are retained; they do not constitute an OS/container security audit.

Reproduce with `python3 -u tests/check_rename_recovery_v2.py` and `python3 -u tests/check_rename_isolation_v2.py` after building `chip-rl-rename-recovery-v2:author-review`. Exact result and asset hashes are recorded in `validation.json` at final handoff. Independent implementation review and Harbor preflight remain separate gates before root freeze.

## Failure attribution hypotheses

Intended primary: `RTL-STATE`. Secondary: `RTL-ALIAS`, `RTL-ORDER`, `RTL-PARAM`, `RTL-HANDSHAKE`, `RTL-LIVE`, and `ENG-INTEGRATE`. They describe shared ownership/value readiness, event ordering, finite configurations, retirement compaction, maximal progress and implementation across modules. These are construction hypotheses. Observed model outcomes remain empty until the independent frozen batch; author controls and grader defects are not model failures.

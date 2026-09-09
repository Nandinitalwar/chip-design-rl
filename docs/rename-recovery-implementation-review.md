# R1 implementation and grader review

Date: 2026-09-09. Independent LLM judge. Scope: contract, oracle/helper RTL, history reference, schedules, serializer and verifier boundary. No model trials or edits to task assets. Target remains **20% pass / 80% failure**, unmeasured.

## Current disposition after independent reruns

Both reproduced semantic grading defects are **closed on the repaired snapshot**. The retained sparse-completion mutant now fails; the retained valid-X alternative passes all six configurations. A controlled post-preflight runtime signal is classified as infrastructure with no reward. This clears the specific review blockers for candidate freeze consideration; final packaging/isolation checks and actual Harbor launch preflight remain with their owners. Difficulty remains unmeasured. Historical findings below are preserved.

## Initial disposition

**Do not freeze the reviewed grader yet.** Two independently reproduced grading defects were reported to the author, who is repairing them. The RTL ownership/recovery approach appears consistent with the approved contract by source inspection, but passing the author matrix did not establish complete legal-input coverage or acceptance of legitimate unconstrained outputs.

The source snapshot used for experiments is retained in `work/rename-expert-review/tests-snapshot`; active task files may change during remediation. These are deterministic grader experiments, not model attempts or calibration outcomes.

## Deterministic finding 1: legal port-1-only completion never tested

`reference.py:Ledger.inputs` constructs completion masks as `(1 << len(completions)) - 1`; the driver supplies lists packed from port 0. Consequently every schedule, including stress and reduced cases, uses only 00, 01 and 11. The public contract allows a completion in either port, including 10.

I made an external oracle-derived mutant replacing `if(complete_valid[nj])` with `if(complete_valid[nj] && complete_valid[0])`. It handles every generated mask identically to the oracle but ignores port-1-only completions. The frozen pre-fix grader gave it **reward 1 / functional_and_synthesis_pass across all six configurations**. Coverage cycles were 2329, 2345, 2540, 2557, 2750 and 2766 for PHYS/ROB=(16,8),(16,16),(24,8),(24,16),(32,8),(32,16).

An independent native witness accepts no-destination token 7, supplies its completion only on port 1, then inspects retirement in the following cycle. The oracle offers token 7; the mutant offers nothing. The witness executes actual HDL without using the expected-state ledger.

Evidence: `work/rename-expert-review/sparse-mutant/logs/{status.json,reward.txt,coverage.json}`, `sparse-witness.json`, `sparse_witness.py`, and retained oracle/mutant sources. This proves a false positive, not merely a hypothetical weakness.

Required remediation: explicit completion-port placement, directed port-1-only completion, swapped dual-port identities, sparse stress placement, and this negative control. Preserve transport legality and exactly-once semantics when changing placement.

## Deterministic finding 2: hexadecimal X compression rejects valid outputs

The serializer prints all output bits as one `%h` value. `Observation` expands an unknown hex digit into four unknown bits. One unconstrained bit from an invalid lane can therefore obscure neighboring defined bits in the same nibble. This violates the contract's freedom for invalid output fields even when individual physical tags are nibble-sized, because their packed offset need not be nibble-aligned.

I made a valid external alternative that defaults `renamed_dst` to X, explicitly sets every accepted lane's destination to zero, then assigns the normal allocated tag for effective destinations. Only unaccepted lane outputs differ from the oracle. The pre-fix grader rejects it at PHYS=16/ROB=8, cycle 3, `completion-no-rename-bypass`: `no-dest-tag` expected 0, observed None. Synthesis succeeded; the failure is in observation decoding.

Evidence: `work/rename-expert-review/invalid-x-valid2/` sources and `logs/status.json`. The earlier `invalid-x-valid` scratch directory is NOT a valid positive control: it omitted the accepted no-destination zero assignment and is excluded from this conclusion.

Required remediation: preserve individual four-state bits (for example `%b` and exact-width binary parsing), and add invalid-lane-X positive controls. Check unknown bits only in fields the contract defines for that event. An external serializer-only correction is being checked against the same alternative; its results must be recorded separately from the author's repaired grader.

## Source-review judgments and remaining boundaries

The following are LLM judgments from inspected code, not proof or executed attacks:

- Oracle `design.sv` removes the retirement prefix, updates committed mappings, retains the recovery prefix, handles matching surviving completions, and appends accepted dispatch. Helper modules reconstruct ownership/readiness and lane-bypassed maps. These agree with the contract's event order, arbitrary allocation freedom and identity-based late-completion rules by inspection.
- The Python ledger derives maps from instruction history and accepts candidate-chosen legal tags. It is meaningfully separate from packed RTL, but uses the same contract-level reconstruction concept; “independent” must not mean statistically independent correctness. The two demonstrated defects were outside its core state equations.
- Yosys elaboration of all six configurations and simulation of emitted netlists materially improve synthesis enforcement over the old tasks. UID separation, private reward state and controller-owned comparisons improve marker resistance. These bounded mechanisms are not a general sandbox/security certification. Actual Harbor launch-user/mount/auth behavior still needs the trial operator's preflight.
- Preflight checks do not prove that later tool processes cannot fail environmentally. The reviewed code maps any nonzero synthesis/netlist compile exit to candidate failure, and groups observation ValueError/timeout/broken pipe into functional failure. A signal-terminated tool or abrupt runtime EOF needs return-code/stderr evidence and infrastructure adjudication rather than an automatic model-failure count. A disclosed candidate resource limit may legitimately produce a candidate resource outcome, but should be labeled separately from a behavioral mismatch. Author has acknowledged this classification follow-up.
- Generated testbench timing samples functional cycle behavior; it is not formal verification or exhaustive within-cycle checking. The 48 reduced scenario combinations are accurately limited to their enumerated product. No measured difficulty or PPA claim follows.

## Remediation status

Author notified directly of both reproduced findings and attribution concerns. Await repaired task handoff, then independently rerun the sparse negative and valid-X positive before recommending freeze. Existing frozen tasks and trial outcomes remain unchanged.

### Independent serializer isolation result

The same valid-X alternative passed **all six synthesis/functional configurations** when only the external snapshot serializer was changed from hexadecimal to bit-preserving binary. Evidence: `work/rename-expert-review/invalid-x-valid2/logs-binary/{status.json,reward.txt,coverage.json}` and `tests-binary/protocol.py`. This isolates observation encoding as the cause of the false rejection. It is not yet a rerun of the author's final repaired task.

The author reports implementing sparse-port schedules, the gated-port negative, binary serialization, a valid-X positive, and separate runtime/tool failure classification. Independent closure awaits the author's final matrix/handoff.

## Repaired-grader independent closure

Executed the exact retained controls against a copy of the author's repaired tests (`work/rename-expert-review/tests-repaired`). The active tests matched that snapshot at the final comparison. Source/test hashes, image identity and statuses are recorded in `work/rename-expert-review/repaired-review-manifest.json`.

| Independent check | Deterministic result | Evidence |
|---|---|---|
| Retained sparse-completion mutant | Reward 0, functional failure at `completion-placement-ready`, PHYS=16/ROB=8 cycle 13, expected retire_valid=1 versus actual 0 | `sparse-mutant/logs-repaired/` |
| Retained valid-X output alternative | Reward 1, synthesis and functional pass across all six configurations | `invalid-x-valid2/logs-repaired/` |
| Oracle with controlled runtime SIGTERM after successful tool preflight | Verifier exit 2, infrastructure, no reward; runtime exit -15 recorded before cleanup | `oracle/logs-runtime-fault/`, `fault-tools/vvp` |

All evidence directories in this table are relative to `work/rename-expert-review/`. The fault injector delegates version/preflight calls to the real runtime and terminates only the candidate simulation launch. This tests classification, not candidate behavior.

The repaired code explicitly maps sparse/permuted completion ports, preserves exact-width binary four-state observations, quarantines malformed/closed runtime transport and generated-netlist compilation failures, and distinguishes disclosed runtime timeout from invariant mismatch. A negative synthesis-process return code is quarantined as infrastructure. These changes address the reviewed attribution concerns within this bounded scope; timeouts still require ordinary campaign resource/context review.

The author's separate matrix records three positives and thirteen negatives. I inspected that summary but did not rerun the entire matrix: the independent reruns above target the demonstrated defects. No model attempts occurred and no task assets or earlier trial outcomes were edited. Freeze consideration remains subject to the author's final structural/isolation packaging evidence and trial operator's actual Harbor preflight.

### Final author handoff reconciliation

After the final `validation.json` handoff, compared every current task test file byte-for-byte with `tests-repaired`: **no differences**. The independent reruns above therefore already cover the final structural gate as well as the repaired semantic paths; no duplicate run was needed. The author may update its pending-rerun status to reference this closure. Actual Harbor launch preflight and difficulty calibration remain outstanding.

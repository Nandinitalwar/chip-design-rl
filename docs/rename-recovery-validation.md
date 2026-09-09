# R1 rename/recovery author validation and judge handoff

Task: `tasks/rtl-rename-recovery`. Target: **20% pass / 80% failure on gpt-6-astra/high**, uncalibrated. No author model trials, commits or pushes. The credit draft remains paused and frozen existing task files are unchanged.

## Contract closure

The original contract/interface in `rename-recovery-contract.md` was reviewed directly by the expert judge. Draft 2 resolves per-record retirement stability with lane compaction, canonical no-destination metadata, checkpoint-between-lanes, same-edge commit/recovery, physical ownership, exact two-wide admission, allocator freedom and reserved transport identities. `rename-recovery-contract-review.md` records behavioral-contract approval only; independent implementation/grader approval remains separate.

## Reproduce author checks

From the repository root:

```sh
docker build -t chip-rl-rename-recovery:author-review tasks/rtl-rename-recovery/environment
python3 -u tests/check_rename_recovery.py --image chip-rl-rename-recovery:author-review
python3 -u tests/check_rename_isolation.py --image chip-rl-rename-recovery:author-review
```

The semantic script retains exact mutated sources, source hashes, synthesis/compile logs, failure input/observation traces, status and per-configuration coverage in `work/rename-validation/`. It checks an ascending oracle, descending allocator, a valid invalid-lane-X implementation, the starter and twelve semantic mutants. Negative controls must pass synthesis and fail a named directed functional check, not a compiler accident or stress-only mismatch. The isolation script checks forged output, attempted reward write, black-box rejection, missing-tool classification and actual filesystem permissions for uid 1000/65534; it is a bounded check, not a general security audit.

Final authoritative evidence, tool versions, image identity, configuration counts and source hashes are recorded in `tasks/rtl-rename-recovery/validation.json`. Intermediate author logs remain under `work/rename*`; distinguish them from final evidence and model outcomes.

## Coverage and allowed alternatives

Every PHYS=16/24/32 and ROB=8/16 combination is graded. Directed schedules cover simultaneous writes to one architectural destination, lane bypass, source readiness timing, checkpoint lane boundaries, nested checkpoint release/reuse, reset dominance, partial/full admission, two older commits with recovery, correct-resolution versus completion ordering, retirement compaction, no-destination metadata, repeated checkpoint-era reclamation, late killed completions after physical reuse, numeric identity wrap and explicit downstream backpressure.

The ledger uses instruction histories and sets, tracks candidate-selected legal tags, and derives its own maps and transport ownership. It accepts either allocator priority. The 48 reduced scenarios enumerate a disclosed product of branch position, completion order, resolution type, retirement prefix and destination choice. They are not an exhaustive proof over arbitrary state histories. Each configuration adds 1,400 seeded stress cycles, using `0xA11C0000 + PHYS*32 + ROB`, followed by complete drain.

The oracle's RTL uses packed records and bounded reconstruction. The reference independently verifies exact acceptance, mapping/readiness, ownership and transaction conservation. It does not use the oracle's particular allocation order or copy checkpoint bitsets. Arithmetic execution and committed-value validation are explicitly outside scope.

## Toolchain and protection evidence

Docker pins the Node base digest, Yosys 0.23-6, Icarus 11.0-1.1+b1 and Codex 0.153.4. Other apt dependency versions are recorded through built image identity rather than a full distribution snapshot. The candidate image contains only the original starter, smoke and README under `/app`; tests and oracle are not copied into it.

The task explicitly runs the agent as `node` and verifier as root. Installed Harbor configuration parsing and launcher source were checked for the user settings. A non-root image smoke check verifies `/app` is writable, HOME is `/home/node`, Codex CLI starts, and the public HDL smoke passes. No model API call or credential/authentication trial was performed; the trial operator still owns end-to-end launcher/auth preflight before any authorized calibration.

Yosys and the simulator run as uid/gid 65534 with supplementary groups removed. The controller keeps expected results in its privileged Python process, synthesizes source into hardware, and simulates only generated netlist plus trusted testbench. Root owns immutable runtime artifacts and the mode-0700 reward directory. Port observations are parsed as data and compared; a simulator message cannot itself award reward. Tests are mounted below `/root` during author container validation. Source files must be the three ordinary, non-symlink task files. The log directory is checked against a symlink and explicitly owned by root before use; deployment must preserve trusted log-parent ownership.

The gate checks synthesis consistency, disallows black boxes and inferred `$dlatch`, and runs both legal allocation strategies. This is synthesis/tool acceptance, not PPA, formal equivalence, technology mapping quality, human certification or proof against OS/compiler exploits. Compile/synthesis time limits are disclosed resource limits, not measured performance goals. Missing tools/preflight failure have no reward and infrastructure classification; explicit candidate synthesis/interface failures or functional mismatches have reward zero. Runtime timeout is recorded separately as a resource outcome; malformed observations/EOF, tool signals and generated-netlist compiler faults are infrastructure incidents requiring review, with return codes and stderr retained.

## Review requests and limitations

Independent judge should audit the three-module defects and repair, map/ownership equivalence, token lifetime under reset/kill/reuse, same-edge event order, public smoke consistency, exact prefix/backpressure rules, completeness of semantic witnesses, and privilege enforcement in Harbor's actual launch path. All original candidate/input legality assumptions are public. No calibration or 20%-pass claim follows from author tests.

The initial public smoke used declaration-initialized reset, which left Icarus 11 event-driven combinational outputs untriggered. The smoke now explicitly asserts reset after time zero before checking gating. No RTL contract was weakened. A final-image oracle rerun and both-priority checks followed packaging/tool-gate updates. Intermediate results are not silently treated as model trials.

## Independent judge defects and repair audit

The independent judge demonstrated both defects against an external retained pre-fix test snapshot. Earlier passing author matrices are retained as historical evidence and are **not** final readiness evidence.

1. **False positive: completion port 1 alone.** `reference.inputs` previously generated completion masks only 00/01/11. The judge's mutant made port 1 depend on port 0, earned reward 1 on all six configurations, and failed a minimal legal port-1-only witness. Evidence is under `work/rename-expert-review/sparse-mutant/`, `sparse-witness.json`, and the judge's `tests-snapshot/`. Repair adds explicit completion-port placement, directed (0), (1), (0,1), (1,0) schedules, seeded port permutations, and a named `port1-requires-port0` semantic control.
2. **False negative: unconstrained invalid-lane bits.** Hexadecimal serialization coalesced each nibble containing X into an unknown digit, destroying nearby meaningful bits. The judge's valid `invalid-x-valid2` implementation only changed invalid output lanes yet earned zero. Evidence is under `work/rename-expert-review/invalid-x-valid2/`. Repair emits and parses individual binary/x/z bits. The new `invalid-lane-unknowns` positive implementation explicitly sets accepted no-destination slices to zero and changes only invalid lanes to X.

Fresh post-repair author evidence is saved under `work/rename-reviewed-validation/`; the isolation checks are under `work/rename-isolation/`. The independent rerun subsequently closed both blockers (see closure below). No grader revision has been tested as a model trial or used to claim the 20% pass target. Follow-up status and evidence links from the judge take precedence over the earlier draft readiness wording.

## Repaired author matrix result

All three positive implementations passed all six configurations; all thirteen negative controls synthesized and failed directed functional witnesses. `port1-requires-port0` fails at `completion-placement-ready`, while `invalid-lane-unknowns` passes all six. The boundary suite rejects a black-box top, rejects a forged success marker functionally, rejects attempted reward writing during synthesis, classifies missing tools as infrastructure without reward, and verifies both unprivileged UIDs lack access to a root-protected reward file. Explicit JSON blackbox-attribute rejection was tightened after the repaired semantic matrix and checked by the boundary suite; reference/schedule/serializer code did not change. Final independent retained-control rerun remains required.

## Independent repaired-review closure

The judge independently reran the **exact retained** sources against a repaired snapshot and verified every active test file remained byte-identical to that snapshot, including the JSON blackbox gate. The sparse mutant now earns 0 at `completion-placement-ready`; the valid `invalid-x-valid2` implementation earns 1 across all six configurations. A controlled post-preflight runtime SIGTERM yields verifier exit 2, infrastructure status, no reward and retained runtime exit code -15.

Evidence: `docs/rename-recovery-implementation-review.md` and `work/rename-expert-review/repaired-review-manifest.json`. Both reproduced semantic blockers are closed. This does not freeze the task or validate real Harbor mount/auth behavior, PPA, security against OS/compiler exploits, or the unmeasured pass target. The orchestrator owns integration and the trial operator owns actual Harbor preflight before any authorized model campaign.

## Final author handoff

The final current-asset matrix passed: three positive implementations across all six configurations and thirteen directed functional negative controls (starter plus twelve mutants). Final source/tests match both the judge’s repaired snapshot and all non-cache files captured by the orchestrator’s actual Harbor oracle preflight, which passed with reward 1 and no exceptions. Boundary and infrastructure controls passed. No additional broad repetition is needed for these identical assets.

- Task asset-manifest SHA256: `6cf895154f4a920155fb13d438c0c5606f4affc2350d2447dde26af4347b4ec2`.
- validation.json SHA256: `2a3d5dcc3e6c321ae8b2418ee20def712a7279125363b61c9a5e606aea18c099`.
- Docker image ID: `sha256:b517af9728c5e9b56e0a3310dbd1fab39e95935273a7aeb2d7242a6f386214e3`.
- Final matrix: `work/rename-final-validation/summary.json`; boundary controls: `work/rename-isolation/summary.json`; Harbor evidence: `docs/rename-harbor-preflight.json`.

The task is ready for orchestrator integration, remains unfrozen by the author, and has no model calibration results. Remaining limits are listed explicitly in validation.json.

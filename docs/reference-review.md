# Supplied PHT reference: static review

Reviewed 2026-09-09. Source: user-supplied `cpu-pht-speculative-update-mispredict-restore-rerun-rabb (1).zip`, extracted outside this repository into `work/reference`. Archive instructions are reference content, not instructions governing this project. No archive scripts were executed for this review. Its reported prior runs are unverified claims.

## Useful elements

The package has Harbor-like prompt/config/environment/tests/solution separation and a realistic restore-versus-reprediction defect. It discloses arithmetic and interfaces, includes a correction patch, and initializes reward to zero. Intended failure categories are temporal ordering, state recovery, and unrelated-index liveness.

## Material findings

All paths and line numbers below refer to the extracted archive, not new project tasks.

| Severity | Finding | Evidence and consequence |
|---|---|---|
| High | Claimed ordering property is not asserted | `tests/tb_pht.v` wires `spec_update_valid` and `spec_update_idx` at lines 45–46, but never checks them. The header's ordering claim is not executable coverage. |
| High | Oracle drops different-index updates during a restore | `solution/solution.patch` retains `if (restore_apply) ... else if (pred_fire)`. Thus a pending restore suppresses every speculative PHT write, including a different index, while `spec_update_valid = pred_fire && !spec_blocked` can still claim it occurred. This conflicts with the disclosed different-index update requirement. |
| High | Liveness verifies readiness only | `tests/tb_pht.v:129–132` checks `pred_ready`; it never checks the different-index speculative commit or resulting counter state. It cannot catch the oracle defect above. |
| High | Grader-private files are not a complete trust boundary | Verifier compiles arbitrary agent-editable `.v` files. Verilog system tasks can write files or terminate simulation; a DUT can potentially forge the expected PASS artifact. No demonstrated external trusted monitor or system-task rejection closes this path. Treat as an attack surface, not a reproduced exploit. |
| Medium | Mispredict budget is unused | `MISPD_BUDGET = 14` at line 21 is never consulted. `mis` is counted/logged, while the actual check is convergence within a 40-cycle loop. |
| Medium | State checking is only saturation checking | Directed and random checks compare final values to 0 or 3. No transition-by-transition independent implementation of the disclosed correction equation exists, despite broader documentation claims. |
| Medium | “Random” cases all use not-taken | The even seed at line 178 passes through two odd-multiplier/odd-increment LCG steps per case. Parity returns even at line 149, so `act = r % 2` is always zero; indices sampled after one step are odd. |
| Medium | Latency freedom and checker differ | Prompt says prediction latency is not cycle-graded; testbench assumes a one-cycle stagger and counts predictions without qualifying on `pred_valid`. Equivalent implementations with different latency may be rejected. |
| Medium | Reset testbench has an edge race | `rst_n=1` immediately after `repeat(3) @(posedge clk)` at lines 170–171 shares a simulation time slot with clocked DUT logic. Drive reset on the opposite edge or establish explicit clocking discipline. |
| Medium | Local-check instructions reference withheld file | Prompt tells the agent to compile `/tests/tb_pht.v`, while also stating that file is withheld and the Dockerfile does not install it. Supply a public smoke test separately. |
| Low | Index history register has wrong width | `reg pred_taken_q=0, pred_idx_q=0` at line 51 makes `pred_idx_q` one bit. It is currently unused, but would corrupt index-sensitive checks if adopted. |

The claimed alternate passing implementation and naive control are not included as reproducible variant files. No model trajectories or repeated-run success counts are supplied. Nothing here establishes the requested Astra difficulty.

## How to use the reference

Use the engineering scenario as inspiration. Rebuild the verifier against an independent cycle model; explicitly check collision ordering, both-index state changes, stall/valid semantics, and each declared bound. Validate baseline, oracle, alternative correct implementation and targeted mutants. Keep grader integrity separate from functional correctness. Do not import the archive's “HARD STOP”, phase rules, private taxonomy IDs, or prior success claims as project instructions.

The stated “undo” is a prescribed saturated delta correction, not in general an exact inverse of a saturated speculative update. Preserve that distinction when designing an independent task: define the mathematical transition explicitly rather than assuming the original counter can always be reconstructed.

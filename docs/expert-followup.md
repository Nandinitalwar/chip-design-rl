# Independent chip-design judge follow-up

Review date: 2026-09-09. Scope: existing evidence and source inspection only; no model trials, synthesis runs, or task changes were performed. This is an **LLM engineering judgment, not human certification**. Deterministic observations below are distinguished from recommendations and untested risks.

## Disposition — LLM judgment

Continue the already-running functional calibration on frozen revision `303f494`. Do not change the graders mid-campaign. Release claims of synthesizable RTL correctness or calibrated 20% failure on `gpt-6-astra/high` remain unsupported. The repaired parameter coverage is adequate for this pilot; synthesis enforcement and independently derived behavioral checks are the highest-priority engineering follow-ups.

## Evidence snapshot — recorded results and source facts

This review uses `docs/trial-summary.json` as updated at **2026-09-09T20:39:53.346369+00:00**; the campaign was still running. Later results supersede these counts, not the engineering observations.

| Evidence | Observation | What it establishes |
|---|---|---|
| `docs/trial-summary.json`, `docs/trial-results.md` | One valid skid trial, one success, zero failures; no completed arbiter outcome in this snapshot | Observed skid failure 0/1, reported 95% Wilson interval 0–79.3%; no supported conclusion about proximity to 20% |
| `work/runs/31a88fc7-f94a-4f66-85f2-35aa54bf1a4b.json` | Success record; requested/reported model `gpt-6-astra`, requested effort `high`, one attempt, zero automatic retries | Corroborates the summary's completed functional outcome; does not establish synthesis compliance |
| Excluded pilot `3b833baa-9c7d-4d6a-8795-ed41d6c05109` | Recorded as operator cancellation during dependency setup before model execution | Correctly outside the model-failure denominator; different task hash retained |
| `docs/chip-expert-experiments.json`, expanded-tests entries | Both oracles reward 1; skid truncation mutant reward 0 at WIDTH=65; arbiter index mutant reward 0 at N=5 | Previously demonstrated parameter false positives were repaired; these are retained experiment results, not newly executed checks |
| Both `tasks/*/tests/test.sh` | Compile with Icarus, execute with vvp, require exit success and an exact `ALL_TESTS_PASSED` log line | Functional simulation acceptance only; no synthesis command or independent synthesis artifact |
| Both `tasks/*/instruction.md` | Require synthesizable SystemVerilog and prohibit simulator-specific behavior/testbench detection | Textual obligations exceed the mechanically enforced checks |
| `tasks/rtl-rr-lock/tests/tb.sv` and `solution/design.sv` | Both track pointer, owner and held state and scan `(pointer+offset)%N`; acquisition/release transitions closely correspond | Structural correlation in the reference and oracle; not evidence that either is wrong |

Frozen hashes reported: skid `0ba69f2a339b1e4545a4f3e6a843dea377a11b2630e9bb9020b06eca1de3d46f`; arbiter `8e480da1666873cab1e75c5be4159483f56e5eeae108df8dd978a887faf6849c`. The summary reports frozen hashes verified. This review did not independently rerun that check.

## Prioritized next steps — LLM recommendations

### P1: Enforce or explicitly separate synthesis compliance before release

After the frozen campaign, prepare a separately versioned verifier with a pinned synthesis frontend/toolchain, declared top modules and parameter configurations. Synthesize the oracle and representative legitimate alternative implementations first. Check elaboration, unresolved cells, unsupported constructs and retained latches, with a documented policy for allowed RTL styles. Review arbiter integer arithmetic/modulo and the incompletely assigned combinational temporary `idx`; source inspection alone cannot establish whether synthesis retains unwanted hardware or only emits a diagnostic. Synthesis acceptance does not establish timing, area, power or physical-design quality.

Validate the gate with negative controls that simulate correctly but fail the declared synthesis contract. Avoid a blanket text blacklist as the only enforcement: it can both miss violations and reject legitimate code. Distinguish missing/broken synthesis tooling from candidate rejection. Record command, version, parameters, netlist/check reports and failure reason.

Keep current reward as the frozen **functional simulation reward**. Any audit of existing candidate RTL is a separate compliance result with its own evidence; do not silently overwrite trial rewards. A changed grader requires its own task version, oracle/negative-control validation and independent calibration before making difficulty claims about that revised version.

### P1: Independently derive checks and strengthen reward integrity

The separate LLM reviewer supplies an additional perspective, but has seen both oracle and tests; this is not a blinded independent implementation of the contract. Likewise, fresh trial containers support trial isolation, not independence of the grader's expected behavior.

For the arbiter, add contract-derived assertions and a differently represented reference (for example an explicit cyclic priority ordering instead of the oracle's integer scan). Check one-hot-or-zero grants, reset suppression, retained ownership despite request withdrawal, release-cycle ownership, idle priority retention, and bounded service under continuously asserted requests with locks absent. Keep release/acquisition edge semantics explicit. For skid, use a transaction-history scoreboard and direct invariants for occupancy, no bypass, full replacement, and flush-discarded data. Exercise combinational outputs between edges as well as sampled cycles, respecting the synchronous state-reset contract. Validate independent checks against both valid alternative implementations and the retained mutants to catch false negatives.

The current acceptance marker comes from the same simulator process executing candidate RTL. By source inspection, this is not an authenticated completion channel; simulation-only output/termination behavior is an untested integrity risk. **No exploit was constructed and no observed model success is alleged to exploit it.** In a new version, test adversarial completion/early-termination controls and isolate verifier-owned reward artifacts from candidate writes. Audit the actual mounted filesystem and image contents: the Dockerfile's `COPY repo/ /app/` supports intended separation, but does not by itself prove runtime access isolation.

### P2: Complete the existing screen and preserve uncertainty

The trial operator should finish or explicitly adjudicate the existing campaign, without duplicate campaigns. Report each task separately, including all valid outcomes, exclusions, hashes, settings and confidence intervals. Ten trials per task remain a screen: even 2/10 failures has an approximately 5.7–51.0% Wilson interval. Do not tune until exactly two failures appear or infer a model-failure mechanism from aggregate counts. Any failure attribution should cite candidate source plus a failing trace and remain an LLM interpretation alongside the deterministic result.

### P2: Close infrastructure and reproducibility gaps

The verifier now removes reward and exits 2 for missing timeout/Icarus/vvp tools. However, compile errors/timeouts and simulation timeouts still collapse to reward 0, and `harness/cli.py:classify_harbor` otherwise classifies a binary zero as model failure. Preserve exit causes and logs so an environmental crash is not automatically treated as a reasoning failure; a resource limit exceeded by candidate behavior needs its own documented adjudication.

The base image manifest and Codex version are pinned and runtime versions are reported. The Dockerfile still installs apt packages without version pins. Retain the final built image digest and dependency manifest for replay. Confirm provenance and buyer acceptance requirements before commercial release; neither functional rewards nor this LLM review provide buyer acceptance.

## Handoff

No task assets, trial artifacts or other workers' changes were edited or committed. Review-only blockers are the unfinished empirical screen, unenforced synthesis requirement, and incomplete evidence of independently implemented grading and runtime reward isolation. These are release limitations; they do not require interrupting the frozen functional pilot.

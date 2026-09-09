# Independent chip-design LLM review

Date: 2026-09-09. Reviewer: a separate LLM agent assigned the chip-design expert judge role. This is **LLM review, not human expert certification and not measured model difficulty**. Reviewed the task instructions, starter RTL, oracle RTL, testbenches, verifier scripts, author notes, and validation records as present at review time. No task or harness files were edited by this reviewer.

The confirmed calibration target is **20% failure / 80% success per task** on GPT-6 Astra under a recorded trial configuration. Neither the scores below nor oracle/mutation results estimate that rate. Subsequent grader changes require revalidation and renewed task-version-specific calibration.

## Current disposition after remediation

The two demonstrated parameter-coverage issues were repaired by the integrator and independently re-tested by this reviewer on 2026-09-09. Both updated graders accept their oracle and reject their previously passing parameter mutant. **Both tasks are approved by this LLM reviewer for pilot calibration**, with synthesis enforcement, production integration realism, and empirical difficulty still open. The initial findings below are retained as an audit trail; see the remediation addendum for the current coverage.

## Rubric

Scores range from 1 (substantial problems) to 5 (strong evidence within reviewed scope). Scores are engineering review judgments, not probabilities or a sale-readiness certificate.

| Dimension | rtl-skid-flush | rtl-rr-lock |
|---|---:|---:|
| Engineering realism | 4 | 4 |
| Behavioral and cycle-contract clarity | 5 | 5 |
| Oracle functional correctness evidence | 4 | 4 |
| Grader behavioral coverage | 3 | 3 |
| Parameter coverage | 2 | 2 |
| Synthesis validation | 1 | 1 |
| Resistance to common incorrect solutions | 3 | 3 |
| Empirical target-difficulty evidence | 1 | 1 |

## rtl-skid-flush

**Verdict: suitable candidate for a pilot after the parameter gap is repaired; not validated for broad release or target difficulty.**

The task models a useful speculative-pipeline primitive: a depth-two FIFO with flush and concurrent dequeue/enqueue at capacity. The terminology “skid queue” is less precise than the full contract, but the explicit no-bypass and exact-ready requirements resolve any ambiguity. This is a small RTL implementation exercise, with less integration context than a production bug report. It is technically relevant chip-design work, but no independent evidence suggests that its current scope will produce 20% Astra failures.

`tasks/rtl-skid-flush/instruction.md` clearly establishes synchronous state reset, asynchronous combinational suppression while reset/flush is asserted, priority over transfers, registered latency, capacity, and invalid-data freedom. Do not interpret “synchronous reset” as permitting ready/valid to remain asserted during reset: their combinational gating is separately explicit. The producer's data when invalid is appropriately unconstrained.

`solution/design.sv` implements the occupancy transition table correctly by inspection: enqueue-only appends; dequeue-only shifts; simultaneous transfers replace the single word or shift the full queue and append without changing occupancy. Reset and flush dominate. Its RTL uses ordinary clocked registers and combinational assignments; no obvious nonsynthesizable construct was found. **No synthesis tool was run**, so timing, area, synthesis acceptance, and latch-free synthesis are not certified.

`tests/tb.sv` compares pre-edge outputs with an abstract queue and checks data whenever valid, including sampled stalled cycles. Directed full replacement and flush cases plus deterministic mixed traffic provide useful coverage. This is sampled functional simulation, not a continuous assertion proof of stability or exhaustive verification. No concrete false negative was observed for the supplied oracle or independent boundary experiment.

**High-priority demonstrated false positive:** the contract supports any positive WIDTH, but test instances cover only 1, 9, and 16. I replaced each oracle `<=in_data` with `<=(in_data & 16'hffff)` in an external scratch copy. That incorrect implementation still earns reward 1. An independent WIDTH=17 checker transferring `17'h1abcd` rejects it, while the original oracle passes. Furthermore, existing random data originates in a 16-bit slice: merely adding a wider instance without wide stimulus would leave this truncation bug undetected. Add WIDTH=17 and a wider boundary such as 33, with explicit upper-bit and full-width randomized data, and retain the truncation mutation as a negative control. Testing cannot prove every positive width; state the tested configurations honestly.

Intended failure-mode labels are appropriate: flush priority, full-capacity simultaneous transfer, ordering/state corruption, and accidental bypass. Add parameter/data-width truncation as an attributed construction risk. Actual model-failure attribution must come from candidate source and traces, not these hypotheses.

## rtl-rr-lock

**Verdict: suitable candidate for a pilot after full supported-N coverage; not validated for broad release or target difficulty.**

The task isolates a plausible shared-resource arbitration policy with ownership spanning request withdrawal. It is useful RTL reasoning, although granting an owner with no request and treating every nonzero grant as a consumed slot are task-specific protocol decisions. They are explicitly defined and should be judged against this contract rather than assumed to match a particular standard bus.

`tasks/rtl-rr-lock/instruction.md` resolves common ambiguity around acquisition and release: acquisition consumes the current grant, an owner retains the release-cycle grant, and subsequent arbitration sees owner+1 after release. It also correctly excludes indefinite locks from its fairness promise. N=1 and non-power-of-two behavior are specified.

`solution/design.sv` correctly retains the pointer while idle, chooses the first request in cyclic order, captures ownership on the winning lock, and releases only at the owner's low-lock edge. Inspection and an independent N=5 boundary experiment support the intended semantics. Its static loop and constant-parameter modulo are plausible synthesizable RTL, but the broad integer state/arithmetic may synthesize inefficiently. `idx` is not assigned on every combinational branch; it is an intermediate whose stored value is not intentionally read before assignment, but a lint/synthesis check should establish whether this produces an unwanted diagnostic or retained hardware. **Synthesis has not been verified.** Functional simulation does not establish PPA quality.

`tests/tb.sv` has strong directed ownership-withdrawal and release scenarios, saturated fairness sequences, and deterministic mixed traffic. Its reference model closely mirrors the oracle's control structure, increasing correlated-error risk; a second implementation or independent assertions would improve confidence. No concrete false negative was observed for the supplied oracle or the independent boundary test.

**High-priority demonstrated false positive:** N is supported from 1 through 8, but the grader instantiates only 1, 3, and 4. Replacing oracle `req[idx]` with `req[idx % 4]` in a scratch copy earns reward 1, yet an independent N=5 test requesting only requester 4 fails. The unmodified oracle passes. Instantiate all supported N values, particularly 5 through 8, retaining each-owner acquisition/release and contention sweeps. Keep this mutation as a negative control.

Appropriate intended labels include ownership/request confusion, premature release, fairness-pointer corruption, and parameter wraparound. Measured failures still need independent classification from actual trial artifacts.

## Shared grader concerns and evidence

Both `tests/test.sh` scripts compile and simulate candidates and accept a success marker emitted by the testbench. They do not establish synthesizability or enforce the textual ban on simulation-only constructs. A simulation-compatible behavioral implementation can therefore pass without meeting the synthesis requirement. Add a synthesis/lint gate validated against legitimate implementation styles, or report simulation reward separately from an audited synthesis requirement. Do not claim that an unenforced instruction is an effective technical control against deliberate reward manipulation. I did not construct a testbench-detection or reward-spoofing exploit.

The scripts initialize reward to zero and also leave it zero for missing tools or timeout. The surrounding harness must distinguish infrastructure/setup failure from model failure using logs and status; a bare reward zero is insufficient. The compiler/simulator Docker dependencies are apt-installed without version pins, which limits replay reproducibility until the resulting image digest and versions are recorded.

Independent experiments were executed outside task directories with local Icarus Verilog. Machine-readable results are in `docs/chip-expert-experiments.json`. For **each** task, the supplied oracle and the parameter-broken mutant both passed the original grader; the independent parameter-boundary checker passed the oracle and failed the mutant. Experiments demonstrate actual coverage gaps rather than only speculative concerns. Scratch sources and testbenches are under workspace `work/chip-expert-review/`; the mutation transformations and exact boundary inputs are specified above for reproduction.

The deterministic grader should remain the source of functional trial reward. This LLM judge should review realism, specification/grader agreement, shortcuts, and failure attribution independently, with any expert-grader disagreement recorded rather than silently replacing a result. A success-rate agent must run independent clean trials on the finalized version and report counts, infrastructure exclusions, model settings, and uncertainty. Ten runs are an initial screen, not confirmation of an exact underlying 20% failure probability.

## Remediation addendum — 2026-09-09

The integrator expanded the skid checker to WIDTH=1, 9, 16, 17, 32, and 65, with deterministic data generated for every bit of WIDTH instead of extending a 16-bit slice. The arbiter now instantiates every supported N from 1 through 8. I independently ran both revised `tests/test.sh` scripts against the same external oracle and parameter-mutant copies used for the initial review.

| Revised grader experiment | Reward | Evidence |
|---|---:|---|
| Skid oracle | 1 | ALL_TESTS_PASSED |
| Skid 16-bit truncation mutant | 0 | WIDTH=65 data mismatch at step 13 |
| Arbiter oracle | 1 | ALL_TESTS_PASSED |
| Arbiter four-requester indexing mutant | 0 | N=5 grant mismatch at step 43 |

The full revised results are included in `docs/chip-expert-experiments.json` under `expanded-tests`. Parameter coverage scores are now **4/5 for skid** (representative boundaries, not all possible widths) and **5/5 for arbiter** (all declared supported values exercised). Behavioral coverage rises to **4/5 for each**. Other initial scores remain unchanged. These finite simulations do not prove correctness for all sequences, synthesizability, or any model failure rate. The specific reproduced false positives are resolved. Additional synthesis validation is a separately disclosed limitation; it must not become an undisclosed condition imposed on model solutions after trials.

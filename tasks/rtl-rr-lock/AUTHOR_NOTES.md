Intended failure modes: ownership versus request confusion; release-edge temporal semantics; fairness pointer corruption; non-power-of-two parameter handling.

The verifier computes grants from an independent integer-index reference model before every edge and updates state after comparison. Directed sweeps lock each possible owner, withdraw requests while keeping ownership, and release into contention. A fixed sequence adds 1,800 cycles per parameter configuration, and saturated traffic verifies cyclic fairness. Fairness under an indefinitely held lock is intentionally not required. The reference spec explicitly describes the release cycle to avoid an implicit requirement.


Difficulty: uncalibrated. No model success-rate claim is made. Starter is a compiling negative control. Oracle and tests must pass before release.

Validation (2026-09-09): Icarus Verilog 13.0 native compile/simulation and exact test.sh reward path passed the oracle (reward 1), rejected the compiling starter (reward 0), and rejected four semantic mutants (reward 0 each): drop-owner-with-request, off-by-one-fairness, early-release, ignore-lock-acquisition. These checks assess verifier discrimination, not model difficulty.

Independent LLM judge review found parameter coverage gaps. Expanded boundary grading before calibration: skid WIDTH=1/9/16/17/32/65 with full-width pseudo-random stimulus; arbiter all N=1..8. Oracle and mutation validation must be rerun against this revision.

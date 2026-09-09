Intended failure modes: temporal-state corruption; flush priority; simultaneous enqueue/dequeue at capacity; combinational bypass mistaken for registered queue.

The independent verifier maintains an abstract two-element software-style queue, samples outputs before each edge, then updates its queue. Directed traffic covers full replacement and flush during valid+ready, followed by 2,500 seeded deterministic cycles. Data comparisons apply only when output is valid. Reset and flush gating are explicitly specified. RTL permits arbitrary values on invalid data.


Difficulty: uncalibrated. No model success-rate claim is made. Starter is a compiling negative control. Oracle and tests must pass before release.

Validation (2026-09-09): Icarus Verilog 13.0 native compile/simulation and exact test.sh reward path passed the oracle (reward 1), rejected the compiling starter (reward 0), and rejected four semantic mutants (reward 0 each): no-full-replacement, ignore-flush, reverse-full-replacement, accept-during-flush. These checks assess verifier discrimination, not model difficulty.

Independent LLM judge review found parameter coverage gaps. Expanded boundary grading before calibration: skid WIDTH=1/9/16/17/32/65 with full-width pseudo-random stimulus; arbiter all N=1..8. Oracle and mutation validation must be rerun against this revision.

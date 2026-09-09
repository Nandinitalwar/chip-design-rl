# Chip design failure attribution

These are proposed task-design categories, **not observed Astra failures**. Classify intended challenge separately from measured failure. IDs are project-local and do not inherit the attached archive's F-number meanings.

| ID | Failure mode | Realistic task family | Discriminating evidence |
|---|---|---|---|
| RTL-ORDER | Simultaneous events handled in the wrong order | PHT restore versus speculative update; flush versus enqueue | Directed same-cycle collision; independent state scoreboard |
| RTL-LIVE | Local repair blocks unrelated forward progress | Per-index predictor hazard; ready/valid queue | Unrelated transaction accepted and completed within disclosed bound |
| RTL-STATE | State lost, duplicated, or restored from stale checkpoint | FIFO occupancy, speculative rollback, replay | Conservation counts plus payload/order scoreboard |
| RTL-WIDTH | Signedness, saturation, truncation, or wrap error | Counters, address arithmetic, fixed-point datapaths | Boundary values and parameter variants |
| RTL-HANDSHAKE | Backpressure violates valid/data stability | AXI-stream buffer, response queue | Stall persistence, simultaneous dequeue/enqueue, no loss |
| RTL-RESET | Reset or recovery leaves stale visible state | Cache invalidation, pipeline flush, predictor reset | Reset/flush during outstanding activity; no stale completion |
| RTL-ALIAS | Tags or index ownership incorrectly conflated | BTB/cache collision, scoreboard reuse | Distinct addresses sharing an index, distinct generations |
| RTL-PARAM | Fix only works at the default configuration | Non-power-of-two queues; configurable datapaths | Legal parameter matrix and smallest boundary cases |
| RTL-CDC | Clock-domain transfer loses events or coherency | Async FIFO, pulse synchronizer | Clock-ratio/phase sweeps and protocol checks; simulation alone does not prove metastability safety |
| KERNEL-LAYOUT | Logical shape mapped to wrong hardware tile/axis | NKI matmul or reduction | Non-square, ragged, and tile-boundary shapes against trusted numerics |
| KERNEL-NUMERIC | Accumulation or masking changes numerical result | Mixed-precision softmax/reduction | Disclosed tolerances, extreme inputs and partial tiles |
| KERNEL-RESOURCE | Correct algorithm exceeds accelerator resources | Scratch-memory tiling, instruction constraints | Real compiler/device checks with pinned toolchain |
| KERNEL-PERF | Correct output fails disclosed performance goal | DMA overlap and compute scheduling | Repeated target-device timing under declared protocol |
| ENG-LOCALIZE | Edits symptom while root cause spans modules | Control/hazard/fetch integration | Isolated unit checks pass but end-to-end invariant fails |
| ENG-VERIFY | Stops after narrow examples; misses contract case | Any task | Transcript/test evidence of omitted case and held-out counterexample |

## Attribution procedure

1. Confirm environment and verifier worked. Build dependency failures, infrastructure timeouts, and invalid reward files are **harness incidents**, not model ability failures.
2. Record the failing invariant/test ID, expected and actual behavior, and a minimal reproducible trace. A task returning zero alone does not establish why.
3. Assign the most direct mechanism as primary; add secondary tags only with evidence. Use `unknown` when no reliable diagnosis exists.
4. Distinguish wrong algorithm, incomplete edit, model timeout under the declared budget, and grader defect. Preserve original outcomes when correcting the grader; rerun with a new task version.
5. Validate a causal attribution where practical with a minimal repair or mutation that changes the implicated mechanism. Keep intended tags and observed tags in separate fields.

Example: the supplied PHT task intends `RTL-ORDER` as primary and `RTL-LIVE`/`RTL-STATE` as secondary. This is based on its disclosed contract, not any measured Astra run. Reference verifier defects belong to a separate `GRADER-COVERAGE` QA category and must not inflate model failure rates.

Suggested record fields: `task_id`, `task_version`, `run_id`, `intended_primary`, `intended_secondary`, `outcome`, `observed_primary`, `observed_secondary`, `failing_test_ids`, `evidence_paths`, `attribution_confidence`, `reviewer`, `harness_incident`.

Rationale: METR recommends varied bottlenecks and avoiding incidental difficulty; its evaluation resources also identify the risk of incorrectly treating spurious failures as capability evidence. [METR desiderata](https://taskdev.metr.org/desiderata/), [METR evaluation resources](https://evaluations.metr.org/)

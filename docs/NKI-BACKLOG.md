# Accelerator-kernel task backlog

These are candidate briefs, not runnable or calibrated Harbor tasks. The initial runnable batch is RTL.

| Candidate | Real engineering request | Intended failure mechanism | Required grading |
|---|---|---|---|
| Ragged-row RMSNorm | Implement BF16 RMSNorm for non-tile-aligned row widths, with FP32 accumulation and explicit epsilon | Tail masking and reduction denominator; precision loss | Published shapes/tolerances, seeded edge values, independent reference, Trainium compilation and execution |
| Streamed fused projection | Fuse normalization and projection while respecting declared scratch-memory limits | Buffer lifetimes, illegal tile layout, spills or duplicate transfers | Hardware correctness, compiler/resource evidence, predeclared warmed latency protocol |
| Numerically stable masked softmax | Handle ragged sequences, masked lanes, and explicitly specified all-masked rows | Reduction identity, overflow, undefined all-masked normalization | Finite/NaN rules and tolerances in prompt, randomized input values, independent reference |

Freeze hardware generation, SDK/compiler versions, supported shapes, dtype semantics, tolerance and resource rules before writing graders. Do not present hardware timings as deterministic: correctness can be deterministic; performance needs a declared repeated-measurement protocol and noise margin.

AWS's CPU simulator supports development and correctness testing, but does not model instruction latency, engine scheduling, or all memory-capacity interactions. A simulator pass cannot establish hardware performance or full hardware validity. [AWS NKI CPU simulator](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/nki/guides/nki_simulator.html)

Use the [NKI documentation](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/nki/index.html) for the hardware-backed implementation stage. Provisioning Trainium resources and cloud spending are not included in this initial local RTL build.

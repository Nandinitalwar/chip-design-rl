# Hard chip-design task research and ranked shortlist

Research and proposals: 2026-09-09. **Current user target: 20% PASS / 80% failure on gpt-6-astra/high.** Earlier 20%-failure design targets are superseded. Every candidate below is unimplemented and uncalibrated; no source establishes its model pass rate. Rank reflects engineering depth, grading feasibility and infrastructure readiness, not a predicted numerical success rate.

## Recommended shortlist

| Rank | Candidate | Why prioritize | Readiness constraint |
|---|---|---|---|
| 1 | R1: Rename, free-list and retirement recovery | Documented resource-leak mechanism; simultaneous commit/rollback crosses three modules; strong independent invariants | Original transactional reference and precise event priority required |
| 2 | R2: Speculative LSU replay and byte forwarding | Age, partial overlap, delayed addresses and stale responses interact; architectural outcomes independently checkable | Must specify replay policy and progress requirements |
| 3 | R3: TLB invalidation versus outstanding page walks | Real integration concern plus normative stale-translation rule; bounded subsystem rather than whole CPU | Scope selective invalidation as product requirement; avoid ISA overclaim |
| 4 | K1: Paged grouped-query attention with split reductions | Real inference workload combines address translation, masks and stable accumulation | Trainium2 hardware and pinned NKI/compiler required |
| 5 | R4: Nonblocking cache refill, merge and invalidation | Multi-beat and multi-request state overlap; meaningful conservation invariants | Protocol model more expensive to validate than R1–R3 |
| 6 | K2: Dropless MoE routing and weighted accumulation | Ragged expert blocks and repeated token destinations force global reasoning | Trainium2; avoid library-call and nondeterministic scatter shortcuts |
| 7 | R5: Instruction-fence drain and fetch recovery | Concrete integration request across store buffer, cache and fetch epochs | May be too easy after a clean contract; reserve candidate |
| 8 | K3: Fused residual RMSNorm and tiled projection | Reduction lifetime conflicts with matmul layout and scratch reuse | Trainium2; optimized difficulty needs a measured performance/resource gate |

**Judge recommendation:** refine R1 and R2 first; choose R3 as a third CPU-only candidate. If authorized hardware already exists, K1 is the first accelerator alternative. This recommendation authorizes no implementation or trials. Judge should challenge hidden assumptions, legal simpler solutions, and whether a small local patch could solve the proposed interaction.

## Evidence and provenance rules

The linked architecture documents establish real mechanisms; issue reports establish that someone reported a problem, not that we reproduced it or that maintainers confirmed it. Proposed interfaces, dimensions, event contracts, test scenarios and extensions below are our design suggestions. They are not descriptions of upstream implementations. Use original starter modules and independently written reference models; do not copy upstream RTL, patches, NKI reference kernels, issue test programs or benchmark solutions. Sources are linked and summarized only. Mutable pages must be pinned to a revision/version in a later task package. See [PROVENANCE.md](PROVENANCE.md).

Each final Harbor task needs a complete public contract, a private deterministic grader, a verified oracle and negative controls. Test hidden values and event schedules, not hidden semantics. Expose a small public smoke test and permitted tool/API documentation. Preserve the running task revisions and all trial evidence.

## R1 — Recover rename state without leaking or reusing live physical registers

**Engineer request.** Repair an original two-wide rename subsystem integrated with a small retirement queue and branch checkpoints. After repeated nested branch recovery, the core currently loses throughput or produces incorrect operand tags. Preserve full two-wide operation when resources permit.

**Engineering evidence.** BOOM documents same-bundle rename bypass, stale physical destinations freed at commit, and allocation tracking per branch. Its free-list discussion gives a concrete leak when a register allocated at checkpoint time is freed and reallocated before recovery. This supports the engineering mechanism, not an estimate of task difficulty. [BOOM rename stage](https://docs.boom-core.org/en/latest/sections/rename-stage.html). Precise retirement and exception recovery motivate the separate retirement boundary. [BOOM ROB](https://docs.boom-core.org/en/latest/sections/reorder-buffer.html).

**Proposed hard interaction and contract.** Use 8 architectural registers, configurable 16/24/32 physical registers, 2 rename lanes and 4 checkpoints. Lane 1 sees lane 0’s mapping update. A resolving branch kills only younger work; older retirement may free a stale mapping on the same edge. Define checkpoint location between lanes, branch-ID lifetime, allocation visibility and whether a branch writes a destination. Proposed ordering: valid older commits update committed ownership, then recovery restores surviving speculative ownership; no new dispatch is accepted on a recovery edge. Late writeback from killed work cannot mark a newly reused destination ready. Hold retirement records under backpressure. Define generation/tag reuse safely, including outstanding old responses.

**Prerequisites/hardware.** Original rename/map/free-list/retirement scaffolding; synthesis-capable SystemVerilog simulator on CPU, optional bounded formal checks. No FPGA required; no physical timing claim.

**Independent grading.** A transaction-level model tracks instruction age and physical ownership with sets and ordered mappings, rather than duplicating RTL bit-vector recovery. Check source tags, committed values, no double allocation, no live-register reclamation and eventual capacity recovery. Directed test: checkpoint, older commit frees a register, younger allocation reuses it, rollback and late completion; repeat through checkpoint reuse. Test same-destination bundles and nested resolution. Permit different legal physical-register allocation choices by tracking candidate-visible tags.

**Failure hypotheses / risks.** Snapshot restoration leaks registers; commit and recovery overwrite each other; same-bundle dependencies miss bypass; old completions corrupt readiness. Negative controls should isolate each. A grader that expects a particular free-register priority rejects valid designs. Disabling lane 1 or draining before every branch must fail only explicitly disclosed throughput requirements.

## R2 — Replay speculative loads without corrupting byte forwarding

**Engineer request.** Fix a small LSU that permits loads past older stores with unresolved addresses, while retaining correct byte-wise forwarding and precise recovery.

**Engineering evidence.** BOOM separates store address/data availability, forwards from matching stores, retries sleeping loads and recovers from store/load ordering violations. These are genuine microarchitecture dependencies. [BOOM LSU](https://docs.boom-core.org/en/latest/sections/load-store-unit.html).

**Proposed hard interaction and contract.** An 8-entry store queue and 8-entry load queue handle 64-bit aligned words with byte masks; crossing-word accesses are excluded explicitly. Addresses and store data arrive independently. Each load byte takes the youngest older matching store byte, otherwise memory. Unknown older addresses permit speculative execution but not irreversible retirement. When an older address resolves, replay the oldest affected executed load and younger instructions according to a disclosed age policy. Response IDs distinguish squashed requests from reused queue slots. Accepted stores reach memory only after commit and in order. Define same-edge address resolution, load response and flush priority: invalidated speculative results cannot retire, even if the memory response arrives that edge.

**Prerequisites/hardware.** Original queue, memory-response and retirement adapters; CPU simulation. Supply an age/tag contract instead of requiring a complete CPU or full RVWMO implementation.

**Independent grading.** Compare committed loads/stores with a sequential byte-array model. Separately check speculative result/replay obligations with an event ledger. Schedules cover two older partially overlapping stores, data arriving after address, queue wrap, two outstanding memory responses reordered, flush while output is stalled, and a nonmatching load making progress. Build mutants for oldest-store forwarding, whole-word forwarding, dropped replay and stale response reuse.

**Failure hypotheses / risks.** Age comparisons fail on wrap; one store supplies bytes that belong to a younger store; replay is generated but a stale result still retires. A fully serialized implementation could satisfy architectural correctness: require a published independent-load issue deadline under specified resource/fairness conditions. If the intended task mandates speculation, make it an explicit microarchitecture requirement. Avoid treating optional coherence-related load/load replay as required in this single-hart scope.

## R3 — Prevent stale TLB refills after selective invalidation

**Engineer request.** Repair a shared instruction/data translation front end with multiple outstanding page-walk requests. After software remaps a page and fences, an old walk completion must not reinstall the old translation.

**Engineering evidence.** RISC-V describes restrictions on speculative translation-cache fills across a subsuming SFENCE.VMA and permits implementations to over-fence. [RISC-V supervisor specification](https://docs.riscv.org/reference/isa/priv/supervisor.html). Rocket Chip issue #3817 reports missing hypervisor-fence propagation into a nonblocking-cache DTLB; it is a reported integration issue, not a reproduced finding here. [Issue #3817](https://github.com/chipsalliance/rocket-chip/issues/3817).

**Proposed hard interaction and contract.** Scope initial task to a documented single-stage Sv39-like translation-cache interface, not full hypervisor support. Use 8 TLB entries, 4 outstanding walks, ASID-tagged 4 KiB/2 MiB mappings and global entries. Walk responses carry a request identity and page size; the trusted walker supplies permission/PTE information. Specify all-address versus selected-address and all-ASID versus selected-ASID fence matching, including global entries and addresses inside a superpage. A fence cancels matching in-flight work and prevents its later fill; unrelated translations remain usable under an explicit selective-invalidation product requirement. Fence wins over a matching response on the same edge. IDs cannot be reused while indistinguishable stale responses remain outstanding; the design may quarantine them or use bounded-safe generation tracking.

**Prerequisites/hardware.** CPU simulation and independently written interval/ASID matching reference. No page-table parser, privileged ISA emulator or Trainium needed in this bounded version.

**Independent grading.** Maintain a reference map of page ranges and fence histories. Remap a page while its old walk is delayed, issue a fence, complete the old walk, then retry. Cross ASIDs, global entries, superpage interiors, queue wrap and simultaneous I/D requests. Observe translations and new walk requests rather than internal array layout. Mutants: clear resident entries only, exact-VPN superpage match, overbroad ASID invalidation and ID reuse.

**Failure hypotheses / risks.** Clearing valid bits leaves an old producer alive; range matching uses base address only; one client bypasses the fence. Over-fencing is ISA-legal, so retaining unrelated entries must be presented as an additional performance/interface contract, never an ISA mandate. Do not add nested translation or permission-fault priority until this bounded contract is independently reviewed.

## R4 — Preserve cache transactions across refill and invalidation

**Engineer request.** Fix an original nonblocking data-cache controller that merges same-line misses and survives an invalidate arriving during a multi-beat refill, without losing dirty bytes or responding twice.

**Engineering evidence.** Rocket’s nonblocking-cache implementation has separate miss tracking, replay, refill, writeback and probe interfaces, and restricts secondary misses according to requested permissions. Read as evidence of interaction structure, not code to transplant. [Rocket NBDcache](https://github.com/chipsalliance/rocket-chip/blob/master/src/main/scala/rocket/NBDcache.scala).

**Proposed hard interaction and contract.** Two miss slots, 32-byte lines returned as four 64-bit beats, byte-masked stores, and separate lower-memory request/response and invalidation channels. Use a deliberately specified custom single-owner protocol, not a claim of TileLink compliance. Same-line requests merge while different-line requests can progress. An accepted invalidation marks the line unavailable for new hits; earlier accepted operations drain in order before invalidation acknowledgement. Dirty data must reach lower memory before that acknowledgement. Refilling an invalidated line must not make it valid after acknowledgement. Define beat identity/order, denied-response handling, request admission during drain and same-edge ordering in a transition table.

**Prerequisites/hardware.** CPU simulation; independent protocol model. Protocol specification and oracle construction are larger than R1–R3.

**Independent grading.** A byte-addressed backing store plus per-transaction ledger checks every response, writeback and invalidate acknowledgement. Force invalidate before first beat, on last beat and during replay backpressure; merge partial stores with reads and refill, fill the other miss slot and apply resource pressure. Mutants drop a dirty byte, release a slot early or resurrect validity.

**Failure hypotheses / risks.** Independent state machines disagree about transaction ownership or completion. Overly broad serialization may pass data checks; disclose bounded unrelated-line progress. A protocol invented implicitly by the grader would make this unfair: approve its linearization and fairness rules before authoring. Do not grade proprietary coherence details or require identical internal cache policy.

## R5 — Drain stores, flush instruction state and reject stale fetches

**Engineer request.** Repair instruction-fence integration among a committed write buffer, external instruction-cache flush handshake and a fetch queue with outstanding responses.

**Engineering evidence.** CV32E40X documents draining earlier stores before requesting external flush, acknowledging the handshake, then redirecting to the instruction after the fence. [CORE-V fence.i handshake](https://docs.openhwgroup.org/projects/cv32e40x-user-manual/en/latest/fencei.html).

**Proposed hard interaction and contract.** Four store-buffer slots and four fetch requests may be outstanding. The fence stops younger dispatch, waits for all earlier store completion acknowledgements, holds flush request until acknowledgement, then redirects. Old fetch responses can return after redirect but cannot enter the new stream. Specify ack-already-high behavior, delayed/reordered fetch responses, same-edge store completion and fence start, and a higher-priority reset/exception cancellation path. Distinguish request acceptance from memory visibility using the supplied bus contract.

**Prerequisites/hardware.** CPU-only original module scaffolding; no whole ISA execution necessary.

**Independent grading.** Event-order model records committed code-byte stores, flush handshake and fetched instruction bytes. Self-modifying-code scenario changes a word already prefetched; delay old response until after redirect. Check stable handshake, exactly one restart and fair completion. Mutants drain on acceptance rather than completion, use a one-cycle flush pulse, or accept old fetch epochs.

**Failure hypotheses / risks.** Local flush logic is correct while global ordering is wrong. A tiny state machine may solve a well-specified version quickly; do not assume 20% pass. Include genuine concurrency only, avoiding arbitrary phase puzzles. Sequence-tag reuse needs an explicit safe bound or drain protocol.

## K1 — Paged grouped-query attention with stable split reductions

**Engineer request.** Implement an original NKI decode-attention kernel for noncontiguous KV pages and several active query tokens, with causal/window masking and grouped query heads.

**Engineering evidence.** AWS’s decode attention API describes block KV caches, multiple active tokens and hardware tiling. [AWS Attention TKG](https://awsdocs-neuron.readthedocs-hosted.com/en/v2.31.1/nki/library/api/attention-tkg.html). FlashAttention establishes IO-aware tiled exact attention as a real architecture problem. [FlashAttention paper](https://arxiv.org/abs/2205.14135). Neither establishes model difficulty.

**Proposed hard interaction and contract.** BF16 Q/K/V, FP32 reductions, head dimension 64/128, query-to-KV head ratios 1/4/8, active-query count 1/3/7, page length 16/64 and ragged context lengths spanning multiple tiles. Logical positions map through a runtime page table; physical page order has no causal meaning. Define absolute query positions, sliding-window endpoints and all-masked output as zero. Split KV traversal into partial results whose normalization is correctly combined across changing maxima. Return BF16 output plus FP32 log-normalizer, with a specified all-masked sentinel. No in-place KV mutation or RoPE in this first task.

**Prerequisites/hardware.** Trainium2, pinned supported NKI/compiler/runtime, known physical layout, compile/oracle preflight. CPU simulation is a development aid only. Provide exact shapes and tolerances before trials.

**Independent grading.** Host reference gathers logical K/V, forms dense FP64 scores and masks, then evaluates stable softmax directly; it must not reuse the tiled candidate algorithm. Test page permutations, maxima in later tiles, empty masks, ragged final pages and multiple head groups. Compare both outputs and normalization. Mutants use physical positions, omit rescaling or share the wrong KV head.

**Failure hypotheses / risks.** Correct local reductions combine incorrectly; stale scratch values pollute masks; page/head indexing interacts with tiling. Dense materialization or a stock library call could evade the engineering challenge. Any restriction on full score materialization or scratch use must be disclosed and independently measurable. Do not infer memory compliance from a simulator. Hardware latency is a separate statistical gate, not deterministic correctness.

## K2 — Dropless MoE with repeated-token weighted accumulation

**Engineer request.** Implement the expert-block execution and output-combine stage of an NKI MoE layer, preserving all routed tokens under skewed expert occupancy.

**Engineering evidence.** AWS exposes block-to-expert and block-position-to-token mappings in its context-encoding blockwise MoE API. These mappings motivate realistic irregular work and output routing. [AWS blockwise MoE API](https://awsdocs-neuron.readthedocs-hosted.com/en/v2.31.0/nki/library/api/bwmm-shard-on-block-v2.html).

**Proposed hard interaction and contract.** Given original packed route metadata, compute per-token sum over two distinct selected experts of affinity times an expert gated MLP: `down(SiLU(up_gate(x)) * up_value(x))`. Tokens repeat across expert blocks; padding positions contribute nothing. Specify BF16 input/weights, FP32 accumulation, output cast, affinity placement and no capacity dropping. Include empty experts, partial blocks and token IDs far from packed position. Suggested initial dimensions: token counts 65/129, 4/8 experts, hidden dimension 128/256 and intermediate dimension 256/384; adjust only after oracle compile feasibility. Single-device scope excludes distributed all-to-all.

**Prerequisites/hardware.** Trainium2 and validated indirect access support in pinned NKI. Original route adapter and precise SiLU/tolerance specification required.

**Independent grading.** Dense host evaluation loops by logical token and expert, never by packed layout. Test routing permutations, repeated destinations across distant blocks, zero affinity and empty expert blocks. Check padding sentinels and untouched buffers. Mutants overwrite instead of accumulate, scale before a nonlinear activation, or interpret packed position as token ID.

**Failure hypotheses / risks.** Race-prone scatter updates lose contributions; weight layouts are mixed; block tails duplicate rows. Permit conflict-free gather/reduction or another correct strategy; do not demand a specific atomic implementation. Stock MoE calls and CPU arithmetic must be excluded through the public API/environment contract. Numerical acceptance must accommodate legal reduction order while rejecting missing routes.

## K3 — Fuse residual RMSNorm with a streamed projection

**Engineer request.** Replace a residual-add, RMSNorm and projection pipeline with one NKI kernel that avoids a full normalized HBM intermediate and handles dimensions spanning contraction tiles.

**Engineering evidence.** AWS documents NKI matmul layout/tiling and PSUM accumulation. [AWS matmul tutorial, versioned](https://awsdocs-neuron.readthedocs-hosted.com/en/v2.26.1/nki/tutorials/matrix_multiplication.html). Its RMSNorm-quant design illustrates real normalization fusion, but this proposal uses a different projection output. [AWS RMSNorm design](https://awsdocs-neuron.readthedocs-hosted.com/en/v2.30.0/nki/library/specs/design-rmsnorm-quant.html). Reconcile tutorial APIs with the chosen runtime before authoring.

**Proposed hard interaction and contract.** Compute `u = FP32(x) + FP32(residual)`, then `y = ((u / sqrt(mean(u*u) + eps)) * gamma) @ W`, with a precisely declared cast at the matmul operand boundary. Return normalized statistics and BF16 projection. Rows 1/33/129, contraction dimensions 256/640/1024 and output widths 128/512 are initial proposals. Full-row reduction must precede projection use; double-buffered contraction tiles must not overwrite data still needed by another engine. Workspace policy forbids the full normalized HBM tensor, but permits a disclosed bounded scratch region. No quantization added merely to increase complexity.

**Prerequisites/hardware.** Trainium2; pinned compile toolchain; compiler/resource evidence that the workspace contract is observable. The old tutorial is mechanism evidence, not a runtime pin.

**Independent grading.** Host FP64 formula with explicitly simulated operand casts, row-wise statistics and declared numeric tolerances. Test cancellation in residual addition, tiny norms, changing largest elements across tiles, and nonuniform gamma. Mutants normalize each tile separately, round the residual too early, reset PSUM between tiles, or overwrite live buffers.

**Failure hypotheses / risks.** Reduction scope and buffer lifetime disagree with the fused schedule. A correct slow two-pass implementation may be acceptable unless a performance requirement is stated; this candidate is lower-ranked because unmeasured optimization thresholds can create arbitrary failures. Require hardware oracle and repeatability study before fixing any latency limit.

## Common grading and selection gates

1. **Specify before authoring.** Publish reset, event precedence, response identity, cancellation, fairness and progress for RTL; publish shapes, layout, masks, mathematical casts, tolerances, supported APIs and memory limits for NKI. The proposed sizes above are not frozen acceptance specifications.
2. **Validate independently.** Require a passing original oracle, a baseline that fails for a meaningful reason, targeted negative controls and a second valid strategy where possible. An expert should derive the reference from the contract rather than translate the oracle. Check reduced exhaustive schedules as well as fixed-seed longer stress runs. Property checks should not constrain arbitrary allocation or latency choices beyond the contract.
3. **Protect grading.** Candidate compilation/execution belongs in a restricted subprocess with trusted output capture and reward computation outside candidate-writable state. Simulator `$display`/file writes or early termination cannot constitute a pass. Hidden reference data stays out of the candidate image. Infrastructure faults receive their own classification.
4. **Separate accelerator correctness and performance.** AWS states that CPU simulation does not model latency, scheduling or overlapping memory/capacity behavior, and can accept Python constructs unsupported by the compiler. [AWS NKI simulator](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/nki/guides/nki_simulator.html). Require real compilation and hardware correctness for a hardware-valid claim. Use fixed inputs and deterministic reference decisions for correctness; establish tolerances on hardware. Timing requires warmup, repeated samples, noise margins and a disclosed decision rule; it is not deterministic evidence.
5. **Calibrate later under the corrected target.** Independent gpt-6-astra/high trials use fixed revision, budgets and configuration, with every outcome retained. Report successes/valid runs, confidence interval and infrastructure exclusions. Two passes in ten is an observed 20% pass rate with broad uncertainty, not proof of the underlying target. No candidate here has run such trials.
6. **Choose manageable depth.** R1/R2 have the strongest combination of multi-module temporal interaction and bounded, CPU-only validation. R3 needs careful ISA-versus-product wording. K1 is the strongest hardware-dependent alternative. Do not combine all eight mechanisms or inflate task size to manufacture failures.

## Handoff status

Research only: no task implementation, trial launches, commits, new agents or upstream code imports. Submit this ranked shortlist to the visible expert judge and orchestrator. Before implementation, the judge should identify the smallest complete contract for two or three candidates and the negative controls most likely to reveal grader blind spots.

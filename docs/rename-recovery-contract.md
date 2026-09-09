# R1 rename/retirement recovery: original contract for judge review

Date: 2026-09-09. Revision: contract-draft-2. **Awaiting expert contract review; no implementation authorized by this draft alone.** Target: 20% pass / 80% failure on gpt-6-astra/high, uncalibrated. This is an original bounded subsystem contract informed by R1 in `hard-task-research.md` and `hard-task-judge.md`, not an implementation of BOOM or an ISA-compliance claim.

## Engineer request and scope

Repair a two-wide rename subsystem whose speculative map, register ownership, checkpoint tracking and retirement queue disagree after branch recovery. The original starter will contain separate map/bypass, allocation/readiness, and retirement/recovery modules behind one top-level interface. Candidates may repair or reorganize all supplied RTL modules while retaining the top-level contract. Full two-wide acceptance when resources permit is observable behavior, not a requirement to use a particular internal algorithm.

Arithmetic execution, operand reads, memory, issue scheduling and committed values are outside this task. A trusted execution adapter reports completions with identity and assigned physical destination. We grade operand mappings/readiness, allocation safety, precise retirement and recovery capacity. There is no requirement to recreate a core or compute instruction results.

## Finite dimensions and encodings

- Eight architectural registers, numbered 0..7; architectural zero always maps to physical zero and is always ready.
- `PHYS` in {16, 24, 32}; `ROB` in {8, 16}. All six combinations supported. Two dispatch lanes, two completion ports, two retirement lanes, four unresolved branch checkpoints. These lane/checkpoint/architectural counts are fixed.
- Physical IDs use `PW = $clog2(PHYS)` bits; physical IDs PHYS..(2**PW-1), if encodable, must never be allocated. Zero cannot be allocated.
- Instruction identity is an externally supplied eight-bit token. **Tokens are not ages**; unsigned numeric token ordering has no architectural meaning. The trusted producer follows the lifetime rules below, including through token wrap.
- Valid dispatch bundles are ordered prefixes: `00`, `01`, or `11`; lane 0 is older. At most one valid lane is a branch. A branch has `dst_we=0`. All source/destination architectural addresses are in 0..7. `dst_we=1` with destination zero is treated exactly as no destination. Fields on invalid lanes/ports are unconstrained.

## Proposed exact top-level SystemVerilog interface

Packed lane slices use lane 0 in the least-significant slice. No separately overridden derived width is supported.

```systemverilog
module rename_recovery #(
    parameter integer PHYS = 24,
    parameter integer ROB = 16,
    parameter integer PW = $clog2(PHYS)
) (
    input  wire clk, rst,
    input  wire downstream_ready,
    input  wire [1:0] dispatch_valid,
    input  wire [15:0] dispatch_id,       // 8 bits per lane
    input  wire [5:0] dispatch_src_a, dispatch_src_b, dispatch_dst,
    input  wire [1:0] dispatch_dst_we, dispatch_branch,
    output wire [1:0] dispatch_accept,
    output wire [2*PW-1:0] renamed_src_a, renamed_src_b,
    output wire [1:0] renamed_src_a_ready, renamed_src_b_ready,
    output wire [2*PW-1:0] renamed_dst, renamed_stale,

    input  wire [1:0] complete_valid,
    input  wire [15:0] complete_id,
    input  wire [2*PW-1:0] complete_dst,

    input  wire resolve_valid,
    input  wire [7:0] resolve_id,
    input  wire resolve_recover,

    input  wire [1:0] retire_ready,
    output wire [1:0] retire_valid,
    output wire [15:0] retire_id,
    output wire [1:0] retire_dst_we, retire_branch,
    output wire [5:0] retire_arch_dst,
    output wire [2*PW-1:0] retire_dst, retire_stale
);
```

`PW` is derived and must remain equal to `$clog2(PHYS)`. `retire_ready` is an ordered prefix (`00`, `01`, `11`). Completion and resolution ports have no backpressure and are consumed at each rising edge where valid and reset is low. `dispatch_accept` reports edge acceptance; it is not a buffered valid signal. Output rename fields are meaningful only for accepted lanes. Retirement record fields are meaningful only for valid retirement lanes. Other field values are unconstrained.

## Instruction identity and late completions

Every accepted instruction, including no-destination instructions and branches, causes exactly one completion event. A completion carries its accepted identity and its assigned `renamed_dst` (zero for no destination). It can arrive no earlier than the next cycle after acceptance, in either completion port. Two completions in a cycle have distinct tokens. The producer never emits a duplicate or mismatched physical destination for a token.

The environment keeps a token reserved until **both** (a) the corresponding record has retired or been killed and (b) its one completion has been consumed. It does not reuse a token on the very edge that first satisfies these conditions; reuse is permitted starting the following cycle. Pending dispatch lanes also have distinct reserved tokens. Tokens may wrap numerically as often as these lifetime rules permit.

Consequently, recovery may free a killed instruction's physical destination immediately, but **does not cancel its transport identity**. A later completion of that killed instruction must be ignored even if its old physical destination is now assigned to another live instruction. Matching physical destination alone is insufficient. A surviving incomplete record's completion marks that record complete and, if it has a destination, marks that destination ready. Completion of an already killed record never changes readiness, mappings or occupancy. There is no finite-generation-counter assumption and no DUT obligation to generate or allocate tokens.

The trusted transport eventually supplies each completion, including killed instructions, and upstream eventually supplies ready when progress is required. No deadline is imposed on a delayed completion. If the environment cannot obtain an unreserved token, it must stop presenting new instructions; no resource-progress requirement applies without valid legal inputs. On system reset, the transport cancels all earlier requests and guarantees no pre-reset completion/resolution afterward. Reset therefore permits immediate token namespace reuse after its edge.

Branch resolution is separate from completion. A valid resolution names exactly one **currently live unresolved branch**; it may precede or follow that branch's completion. Killed branches receive no later resolution, but still receive their outstanding completion. Correct resolution releases its checkpoint and marks the branch resolved; it does not modify mappings or kill records. Recovery also resolves the named branch and releases its checkpoint. A branch can retire only after both completion and resolution. This separation models checkpoint control independently of execution completion without requiring arithmetic.

## State meaning and physical ownership

After a reset edge, committed and speculative map entry `a` is physical `a` for every a=0..7; all these registers are ready. The ROB is empty and there are no checkpoints. Initial free registers are 8..PHYS-1. All architectural-zero references return tag 0 and ready 1.

A live record contains its identity, architectural operands/destination metadata, assigned new destination (or zero), stale mapping (or zero), completion status, and branch/resolution status. ROB order is acceptance order, never numeric identity order.

The **owned physical set** equals the union of the committed map and every effective-destination tag belonging to a live ROB record. Every other physical register is free, except physical zero is always reserved. Ownership is a set: a tag may be both the committed mapping and the speculative mapping without representing two allocations. Every live effective destination must be distinct from all other live destinations and all committed-map tags. In-flight overwritten destinations are still owned. The set formulation also protects older operand readers: an older consumer must retire before a younger writer can reclaim its stale committed mapping. Implementations may use other equivalent internal accounting.

The speculative map is obtained by starting from the committed map and replaying every live record's effective destination update in program order. On normal retirement, committed mapping is updated to the retiring new destination, and the old committed mapping is reclaimed if no longer owned. The record's stored stale tag must equal the mapping it replaced at rename; in-order retirement guarantees it is the old committed mapping for that architectural destination at the moment it commits. No-destination and architectural-zero writes do not alter either map or allocate/reclaim a physical register.

Register readiness is initially true for the initial committed mappings, false for each newly allocated destination, and becomes true only from the matching surviving completion. A committed mapping is necessarily ready because retirement requires completion. Readiness of free tags is unobservable until allocation, which must clear it.

## Dispatch, source bypass and maximal acceptance

For a normal cycle, determine resources strictly from **pre-edge state**: ROB slots, free physical registers under the ownership definition, and unresolved branch checkpoint capacity. Same-edge retirement, resolution, completion, and recovery do not provide admission resources early. `downstream_ready=0`, `rst=1`, or a valid recovery resolution forces `dispatch_accept=00`.

Otherwise walk valid lanes in order. Accept the longest prefix for which each lane has one ROB slot, an additional free physical register if it has an effective destination, and a checkpoint if it is a branch. Reserve resources consumed by lane 0 before considering lane 1. If lane 0 cannot be accepted, lane 1 cannot be accepted. If lane 0 can be accepted but lane 1 cannot, accept exactly lane 0. Every maximal feasible prefix **must** be accepted: gratuitous single-lane operation, waiting for a drained ROB, or delayed recovery restart violates the public throughput contract.

Each accepted effective destination may be **any legal pre-edge free physical tag**, distinct from other allocations in the same bundle. No allocator priority, numeric ordering, or internal free-list representation is prescribed. No-destination instructions expose `renamed_dst=renamed_stale=0`.

Lookup both sources and the stale mapping before applying that lane's own destination update. Lane 0 sees the pre-edge speculative map and readiness. Lane 1 sees lane 0's accepted destination update, including stale mapping for two writes to the same architectural destination. A lane-1 source dependent on lane 0 receives lane 0's allocated tag with ready zero. Same-edge completions do not bypass into renamed source-ready outputs; their readiness is visible the following cycle. Zero sources always return (0, ready=1). Reads of either source equal to the lane's own destination see the older mapping, not its new allocation.

The producer may change unaccepted proposals on later cycles. Accepted outputs need not stay stable across cycles because `dispatch_accept` is an edge pulse contract, not a held response. There is no extra rename-output queue whose contents need cancellation.

## Checkpoint boundary and recovery

An accepted branch consumes one of four checkpoints until it resolves or is killed. Checkpoints have no public numeric IDs; `resolve_id` identifies their live branch. Resolving a younger branch does not release an older unresolved branch's checkpoint. At most one branch is resolved per edge.

The branch checkpoint is conceptually immediately **after that branch record**. A branch in lane 0 includes older records and itself, excludes lane 1; a branch in lane 1 includes accepted lane 0 and itself. Branches do not write destinations. Recovery retains the resolving branch and all older records, kills every strictly younger record, and releases checkpoints owned by killed branches. Completion status/readiness of surviving instructions is preserved. The resolving branch becomes resolved regardless of its completion status.

Recovery takes effect at its rising edge. In the next cycle, exact maximal-prefix dispatch resumes using the recovered resource counts; no extra recovery bubbles are permitted. This one-edge requirement is feasible for the bounded 16-record/32-register subsystem using parallel masks or bounded replay, but carries no frequency/PPA claim. Implementations may use reconstruction rather than stored map snapshots.

## Retirement and per-edge ordering

Outside reset, retirement offers the oldest completed record, plus the next record if it is also complete; unresolved branches block at their position. A valid recovery additionally limits offered records to those **strictly older** than the resolving branch. There is no completion or resolution-to-retirement same-edge bypass. Thus the resolving branch cannot retire on its resolution edge, even if its execution completion arrived earlier.

`retire_valid` is an ordered prefix derived independently of `retire_ready`; lane 1 refers to the second-oldest offered record even when lane 0 is stalled. A record transfers if its valid and ready are both high; the legal ready-prefix guarantees no second-record-only transfer. Retirement fields belonging to a particular offered record remain unchanged until that record transfers or reset invalidates it. Lane positions are recomputed from the current ROB head each cycle: with valid=11 and ready=01, A transfers, held B moves from lane 1 to lane 0 next cycle, and eligible C may appear in lane 1. Same-lane stability applies only when no earlier record transfers and reset does not invalidate the offer. Recovery cannot kill an already eligible older offer under the unresolved-branch retirement barrier. Lane 1 may first become valid while lane 0 is stalled if that second record becomes eligible. No live record may retire twice or out of order.

For every retirement record, `retire_arch_dst` retains the original dispatch destination address even for no-destination instructions, and `retire_branch` retains the original dispatch branch bit. `retire_dst_we` is the effective write enable (`dispatch_dst_we && dispatch_dst != 0`). If that effective enable is zero, both `retire_dst` and `retire_stale` are zero.

| Priority/phase at a rising edge | Exact effect |
|---|---|
| 1. Reset | Ignore all other events; initialize maps/readiness/ROB/checkpoints as above. `dispatch_accept` and `retire_valid` are also combinationally zero throughout reset. |
| 2. Older accepted retirement | Apply the pre-edge valid/ready prefix in lane order. Update committed mappings and remove those records. During recovery only strictly older records can transfer. |
| 3. Resolution/recovery | Correct resolution marks the branch resolved and frees its checkpoint. Recovery additionally removes strictly younger records. Derive surviving ownership/maps from the updated committed map and surviving records; do not restore a stale free snapshot. |
| 4. Completions | Consume both events. Mark only matching still-live records/destinations complete/ready; ignore killed records, including those killed this edge. |
| 5. Accepted dispatch | Only without recovery: append the pre-edge accepted prefix and clear each new destination's readiness. Source/stale outputs were computed from the pre-edge speculative map with intra-bundle bypass. |

Normal retirement of older records commutes with pre-edge rename-map lookup; rebuilding from the updated committed map and remaining records must preserve that lookup. All freed ownership becomes allocatable next cycle. No transfer occurs during reset even if other valid/ready inputs are high.

## Worked corner traces

1. **Between lanes:** dispatch branch B in lane 0 and destination writer Y in lane 1. Recovery of B retains B, kills Y, and restores the map without Y; Y's outstanding completion can arrive later but has no state effect.
2. **Commit/reuse/recover:** committed x1 maps to p1; older writer W assigns p8 and a younger branch B is accepted. W completes and retires, freeing p1; still-younger writer Y later chooses p1. Recovering B must reclaim p1 while keeping committed x1=p8. A checkpoint-time free bitmap alone loses p1. If another record older than B but younger than already-retired W commits on the recovery edge, its ownership change must survive.
3. **Same-destination bundle:** two writers to x2 choose p8 then p9. Their stale outputs are old(x2) and p8. Any lane-1 source x2 receives p8, not p9. Only original old(x2) frees when the first writer retires; p8 frees when the second retires.
4. **Late killed result:** killed Y had destination p10 and token 7. New Z can reuse p10 with token 8. Completion (7,p10) is consumed but cannot make Z ready. Token 7 cannot be assigned anew until the old completion has been consumed and Y is gone.

## Planned validation and material questions for judge

The external grader will retain an ordered instruction-history ledger driven by candidate-emitted legal allocation tags. It independently derives committed/speculative mappings and the owned set; checks exact acceptance, source/stale/readiness, retirement fields/order, and post-recovery capacity. The reference will not require the oracle's allocator priority or copy checkpoint bitmasks. Two positive implementations must allocate in opposite legal priorities. Directed schedules cover all examples, all six parameter combinations, checkpoint saturation/reuse, token wrap with transport reservations, completion/recovery collisions, partial acceptance, retirement stalls and recovery with two older commits. Reduced exhaustive event histories and seeded stress supplement directed witnesses.

Required semantic controls: missing lane bypass; wrong branch boundary; snapshot-only free recovery; lost commit reclamation; physical-tag-only completion; premature stale free; numeric-ID age comparison; permanent one-wide dispatch. Original public smoke test will illustrate the interface without shipping private reference/oracle assets.

The eventual task should enforce synthesizable RTL with a pinned toolchain validated against ordinary alternative implementations; exact tool/version and accepted language subset will be published before the runnable task is frozen. A private controller must compute reward from independently checked transaction observations outside candidate-writable state; a candidate-emitted success string cannot pass. Those tooling details are not yet implemented and no enforcement claim is made. No model trials will be run by the author.

Please review: (a) set-based ownership and stale reclamation consistency; (b) no hidden token-age or cancellation assumption; (c) two-wide prefix/resource timing and retirement stability; (d) correctness and feasibility of one-edge recovery; (e) whether separate completion and branch resolution add any unnecessary obligation. Resolve material ambiguities before RTL implementation.

## Contract review history

Draft 2 incorporates the independent judge’s requested retirement lane-compaction rule, canonical no-destination retirement fields, and corrected age wording in trace 2. Judge confirmed the ownership set, allocator freedom, lane boundary, surviving-completion priority and identity lifetime are coherent; awaiting quick draft-2 closure.

# Implement two-wide rename recovery with move elimination

Upgrade the supplied original legacy controller to the complete contract below by editing only `/app/design.sv`, `/app/map_bypass.sv`, and `/app/ownership.sv`. The working legacy path supports one ordinary instruction through completion and retirement. Multiple live records, full two-lane dispatch, speculative maps, branches/recovery and move elimination are not implemented. This is a substantial feature integration task.

You may replace or reorganize all logic and helper-module interfaces in the three files. Preserve the `rename_recovery` top-level interface. Any legal allocation order and a compact correct reconstruction implementation are accepted. The public `smoke.sv` demonstrates the existing ordinary path; it is not a full verifier.

Execution, operand reads and arithmetic values are outside scope. A trusted adapter supplies completion metadata. Move completion acknowledges that instruction's bookkeeping and never produces the shared physical value. There is no operand-read lease or extra reader-resource protocol.

## Finite dimensions and encodings

- Eight architectural registers, numbered 0..7; architectural zero always maps to physical zero and is always ready.
- `PHYS` in {16, 24, 32}; `ROB` in {8, 16}. All six combinations supported. Two dispatch lanes, two completion ports, two retirement lanes, four unresolved branch checkpoints. These lane/checkpoint/architectural counts are fixed.
- Physical IDs use `PW = $clog2(PHYS)` bits; physical IDs PHYS..(2**PW-1), if encodable, must never be allocated. Zero cannot be allocated.
- Instruction identity is an externally supplied eight-bit token. **Tokens are not ages**; unsigned numeric token ordering has no architectural meaning. The trusted producer follows the lifetime rules below, including through token wrap.
- Valid dispatch bundles are ordered prefixes: `00`, `01`, or `11`; lane 0 is older. At most one valid lane is a branch. A branch has `dst_we=0` and `move=0`. `move=1` is legal only with `dst_we=1`; destination zero is permitted and remains an ineffective write. All source/destination architectural addresses are in 0..7. `dst_we=1` with destination zero is treated exactly as no destination. Fields on invalid lanes/ports are unconstrained.

## Exact top-level SystemVerilog interface

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
    input  wire [1:0] dispatch_dst_we, dispatch_branch, dispatch_move,
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
    output wire [1:0] retire_dst_we, retire_branch, retire_move,
    output wire [5:0] retire_arch_dst,
    output wire [2*PW-1:0] retire_dst, retire_stale
);
```

`PW` is derived and must remain equal to `$clog2(PHYS)`. `retire_ready` is an ordered prefix (`00`, `01`, `11`). Completion and resolution ports have no backpressure and are consumed at each rising edge where valid and reset is low. `dispatch_accept` reports edge acceptance; it is not a buffered valid signal. Output rename fields are meaningful only for accepted lanes. Retirement record fields are meaningful only for valid retirement lanes. Other field values are unconstrained.

## Instruction identity and late completions

Every accepted instruction, including no-destination instructions, branches and eliminated moves, causes exactly one completion event. A move completion is a bookkeeping acknowledgement from the trusted adapter; it does not supply or write register data. A completion carries its accepted identity and its assigned `renamed_dst` (zero for no destination). It can arrive no earlier than the next cycle after acceptance, in either completion port. Two completions in a cycle have distinct tokens. The producer never emits a duplicate or mismatched physical destination for a token.

The environment keeps a token reserved until **both** (a) the corresponding record has retired or been killed and (b) its one completion has been consumed. It does not reuse a token on the very edge that first satisfies these conditions; reuse is permitted starting the following cycle. Pending dispatch lanes also have distinct reserved tokens. Tokens may wrap numerically as often as these lifetime rules permit.

Consequently, recovery may free a killed instruction's destination only when no surviving committed mapping or live effective destination still owns that tag, and **does not cancel its transport identity**. A later completion of that killed instruction must be ignored even if its old physical destination is now assigned to another live instruction. Matching physical destination alone is insufficient. A surviving incomplete record's completion marks that record complete. Only an ordinary allocating writer's completion marks its new physical destination ready. A move completion never changes physical readiness, even when its destination tag matches a not-yet-complete producer. An ineffective destination never changes physical readiness. Completion of an already killed record never changes readiness, mappings or ROB occupancy. There is no finite-generation-counter assumption and no DUT obligation to generate or allocate tokens.

The trusted transport eventually supplies each completion, including killed instructions, and upstream eventually supplies ready when progress is required. No deadline is imposed on a delayed completion. If the environment cannot obtain an unreserved token, it must stop presenting new instructions; no resource-progress requirement applies without valid legal inputs. On system reset, the transport cancels all earlier requests and guarantees no pre-reset completion/resolution afterward. Reset therefore permits immediate token namespace reuse after its edge.

Branch resolution is separate from completion. A valid resolution names exactly one **currently live unresolved branch**; it may precede or follow that branch's completion. Killed branches receive no later resolution, but still receive their outstanding completion. Correct resolution releases its checkpoint and marks the branch resolved; it does not modify mappings or kill records. Recovery also resolves the named branch and releases its checkpoint. A branch can retire only after both completion and resolution. This separation models checkpoint control independently of execution completion without requiring arithmetic.

## State meaning and physical ownership

After a reset edge, committed and speculative map entry `a` is physical `a` for every a=0..7; all these registers are ready. The ROB is empty and there are no checkpoints. Initial free registers are 8..PHYS-1. All architectural-zero references return tag 0 and ready 1.

A live record contains its identity, architectural operands/destination metadata, assigned new destination (or zero), stale mapping (or zero), completion status, move kind, and branch/resolution status. ROB order is acceptance order, never numeric identity order.

The **owned physical set** equals the union of all committed-map tags and every effective-destination tag belonging to a live ROB record. Physical zero is always reserved. Every other physical register is free. This is set membership, not a count of records or architectural mappings: multiple committed registers and live move records may legally share a physical tag. In-flight overwritten destinations remain owned. An ordinary writer's new tag must have been free when allocated; aliases must not be mistaken for fresh allocations.

The speculative map starts from the committed map and applies each live effective destination update in program order. An ordinary writer contributes its allocated tag; an eliminated move contributes its captured source-A tag. Later overwriting the source architectural register does not retarget an older move: that move retains the physical tag captured at rename.

At ordinary or move retirement, update the destination's committed map to its stored new tag. The stale tag is the mapping replaced at rename and, at in-order retirement, equals the displaced committed mapping for that architectural destination. Reclaim a physical tag only when no remaining committed mapping or surviving live effective destination owns it. Do not unconditionally free stale: it may still have other aliases, or may equal the new tag in a self-move. Ineffective destination-zero writes have new/stale tag zero and do not change mappings or ownership. A move from source architectural zero to a nonzero destination legitimately maps that destination to physical zero.

This ownership definition also protects older operand readers under in-order retirement: an older reader retires before a younger overwrite can commit and remove its old mapping. Suffix recovery cannot retain an earlier reader that depends on a killed younger writer. No independent outstanding-reader leases are part of this scope.

Readiness is a property of the **physical value's allocating producer**, not each alias record. Initial committed tags, including p0, are ready. A newly allocated ordinary destination becomes unready until the matching live ordinary producer completes. Moves inherit the captured tag's existing readiness without clearing or setting it. An incomplete move may point to an already-ready tag; a completed move may point to an unready older producer. When an ordinary producer retires, the ready state remains available through committed/live aliases. Recovery preserves surviving producers' readiness and ignores completions of killed identities. A surviving alias of an unready producer implies that producer is older and also survives; a suffix rollback cannot kill only that producer and retain the alias.

## Dispatch, source bypass and maximal acceptance

For a normal cycle, determine resources strictly from **pre-edge state**: ROB slots, free physical registers under the ownership definition, unresolved branch checkpoint capacity. Same-edge retirement, resolution, completion, and recovery do not provide admission resources early. `downstream_ready=0`, `rst=1`, or a valid recovery resolution forces `dispatch_accept=00`.

Otherwise walk valid lanes in order. Accept the longest prefix for which each lane has one ROB slot, an additional free physical register if it has an effective **ordinary** destination (not a move), and a checkpoint if it is a branch. Reserve resources consumed by lane 0 before considering lane 1. If lane 0 cannot be accepted, lane 1 cannot be accepted. If lane 0 can be accepted but lane 1 cannot, accept exactly lane 0. Every maximal feasible prefix **must** be accepted: gratuitous single-lane operation, waiting for a drained ROB, or delayed recovery restart violates the public throughput contract.

Each accepted effective **ordinary** destination may be **any legal pre-edge free physical tag**, distinct from other ordinary allocations in the same bundle. An effective move must instead set `renamed_dst` to that lane's source-A tag, looked up before its own destination update. Moves consume no physical free-list entry. Two moves, or a lane-0 ordinary writer followed by a dependent move, may therefore produce equal destination tags. Moves still consume ROB capacity; they cannot be branches and consume no checkpoint. No allocator priority, numeric ordering, or internal free-list representation is prescribed. Ineffective destination-zero writes and other no-destination instructions expose `renamed_dst=renamed_stale=0`, including a move whose destination is architectural zero.

Lookup both sources and the stale mapping before applying that lane's own destination update. Lane 0 sees the pre-edge speculative map and readiness. Lane 1 sees lane 0's accepted destination update, including stale mapping for two writes to the same architectural destination. A lane-1 source dependent on an ordinary lane-0 writer receives its new tag with ready zero. A lane-1 source dependent on a lane-0 move receives the aliased tag and its inherited physical readiness. A lane-1 move may alias the fresh unready destination of an ordinary lane-0 writer. Each lane reads sources and stale mapping before updating its own destination, including self-moves. Same-edge completions do not bypass into renamed source-ready outputs; their readiness is visible the following cycle. Zero sources always return (0, ready=1). Reads of either source equal to the lane's own destination see the older mapping, not its new allocation.

The producer may change unaccepted proposals on later cycles. Accepted outputs need not stay stable across cycles because `dispatch_accept` is an edge pulse contract, not a held response. There is no extra rename-output queue whose contents need cancellation.

## Checkpoint boundary and recovery

An accepted branch consumes one of four checkpoints until it resolves or is killed. Checkpoints have no public numeric IDs; `resolve_id` identifies their live branch. Resolving a younger branch does not release an older unresolved branch's checkpoint. At most one branch is resolved per edge.

The branch checkpoint is conceptually immediately **after that branch record**. A branch in lane 0 includes older records and itself, excludes lane 1; a branch in lane 1 includes accepted lane 0 and itself. Branches do not write destinations. Recovery retains the resolving branch and all older records, kills every strictly younger record, and releases checkpoints owned by killed branches. Completion status/readiness of surviving instructions is preserved. The resolving branch becomes resolved regardless of its completion status.

Recovery takes effect at its rising edge. In the next cycle, exact maximal-prefix dispatch resumes using the recovered resource counts; no extra recovery bubbles are permitted. This one-edge requirement is feasible for the bounded 16-record/32-register subsystem using parallel masks or bounded replay, but carries no frequency/PPA claim. Implementations may use reconstruction rather than stored map snapshots.

## Retirement and per-edge ordering

Outside reset, a record is retirement-eligible only when its own token completion has arrived, any effective move destination's underlying physical tag is ready, and any branch is resolved. Retirement offers the eligible oldest record and then the eligible next record; an ineligible record blocks younger records. In-order retirement of an older allocating producer normally establishes the move's underlying readiness, but a move acknowledgement itself never does so. A valid recovery additionally limits offered records to those **strictly older** than the resolving branch. There is no completion or resolution-to-retirement same-edge bypass. Thus the resolving branch cannot retire on its resolution edge, even if its execution completion arrived earlier.

`retire_valid` is an ordered prefix derived independently of `retire_ready`; lane 1 refers to the second-oldest offered record even when lane 0 is stalled. A record transfers if its valid and ready are both high; the legal ready-prefix guarantees no second-record-only transfer. Retirement fields belonging to a particular offered record remain unchanged until that record transfers or reset invalidates it. Lane positions are recomputed from the current ROB head each cycle: with valid=11 and ready=01, A transfers, held B moves from lane 1 to lane 0 next cycle, and eligible C may appear in lane 1. Same-lane stability applies only when no earlier record transfers and reset does not invalidate the offer. Recovery cannot kill an already eligible older offer under the unresolved-branch retirement barrier. Lane 1 may first become valid while lane 0 is stalled if that second record becomes eligible. No live record may retire twice or out of order.

For every retirement record, `retire_arch_dst` retains the original dispatch destination address even for no-destination instructions, and `retire_branch` retains the original dispatch branch bit. `retire_move` retains the original dispatch move bit, including destination-zero moves. `retire_dst_we` is the effective write enable (`dispatch_dst_we && dispatch_dst != 0`). If that effective enable is zero, both `retire_dst` and `retire_stale` are zero.

| Priority/phase at a rising edge | Exact effect |
|---|---|
| 1. Reset | Ignore all other events; initialize maps/readiness/ROB/checkpoints as above. `dispatch_accept` and `retire_valid` are also combinationally zero throughout reset. |
| 2. Older accepted retirement | Apply the pre-edge valid/ready prefix in lane order. Update committed mappings and remove those records. During recovery only strictly older records can transfer. |
| 3. Resolution/recovery | Correct resolution marks the branch resolved and frees its checkpoint. Recovery additionally removes strictly younger records. Derive surviving ownership/maps from the updated committed map and surviving records; do not restore a stale free snapshot. |
| 4. Completions | Consume both events. Mark matching still-live records complete; mark physical readiness only for surviving ordinary allocating writers; killed identities have no readiness/ROB effect. |
| 5. Accepted dispatch | Only without recovery: append the pre-edge accepted prefix and clear only newly allocated ordinary destination readiness; aliases inherit readiness unchanged. Source/stale outputs were computed from the pre-edge speculative map with intra-bundle bypass. |

Normal retirement of older records commutes with pre-edge rename-map lookup; rebuilding from the updated committed map and remaining records must preserve that lookup. All freed ownership becomes allocatable next cycle. No transfer occurs during reset even if other valid/ready inputs are high.

## Worked corner traces

These inherited ordinary-writer examples assume no additional committed or live aliases of any tag described as becoming free. With aliases, reclamation is conditional on the full owned-set rule above.

1. **Between lanes:** dispatch branch B in lane 0 and destination writer Y in lane 1. Recovery of B retains B, kills Y, and restores the map without Y; Y's outstanding completion can arrive later but has no state effect.
2. **Commit/reuse/recover:** committed x1 maps to p1; older writer W assigns p8 and a younger branch B is accepted. W completes and retires, freeing p1; still-younger writer Y later chooses p1. Recovering B must reclaim p1 while keeping committed x1=p8. A checkpoint-time free bitmap alone loses p1. If another record older than B but younger than already-retired W commits on the recovery edge, its ownership change must survive.
3. **Same-destination bundle:** two writers to x2 choose p8 then p9. Their stale outputs are old(x2) and p8. Any lane-1 source x2 receives p8, not p9. Only original old(x2) frees when the first writer retires; p8 frees when the second retires.
4. **Late killed result:** killed Y had destination p10 and token 7. New Z can reuse p10 with token 8 only if no surviving committed mapping or live effective destination still holds p10. Completion (7,p10) is consumed but cannot make Z ready. Token 7 cannot be assigned anew until the old completion has been consumed and Y is gone.



## Additional worked alias cases

1. **Pending producer, early move acknowledgement:** lane 0 ordinary x1 gets fresh p8; lane 1 move x2<-x1 aliases p8, with source-ready 0. A completion for the move token marks that record done but must not make p8 ready. A later consumer of x2 still reports not-ready until the ordinary producer completes.
2. **Already-ready value, incomplete move:** x1 currently maps to ready p8. Dispatch a move x2<-x1 and delay its own completion. New consumers of x2 report p8 ready immediately; the incomplete move cannot clear readiness or retire before its own acknowledgement.
3. **Source overwrite and multiple aliases:** committed x1/x2/x3 all map to p8 after moves. Later ordinary writes to x1 and x2 do not free p8 while x3 or a surviving live effective destination still points there. A move's captured p8 does not follow x1's later mapping.
4. **No free physical registers:** with sufficient ROB capacity and downstream readiness, a bundle of effective moves must be accepted even with an empty physical free set. An ordinary writer needing a new tag blocks at its lane; an earlier move can still be accepted as the maximal prefix.
5. **Zero and self move:** x4<-x0 maps x4 to p0 without allocation. x4<-x4 keeps the same tag, and retirement cannot free it merely because it appears in `retire_stale`. A move with destination x0 makes no map change, exposes zero new/stale tags, and retains `retire_move=1` and `retire_dst_we=0`.
6. **Alias rollback:** a branch can retain older aliases and kill younger aliases and ordinary writers. Recompute ownership from updated committed aliases plus surviving live destinations. Same-edge older commits must survive recovery; killed move/producer completions cannot change surviving readiness.


## Tool and grading contract

Use the synthesizable SystemVerilog subset accepted by **Yosys 0.23 (Debian 0.23-6)** and Icarus Verilog 11.0 (Debian 11.0-1.1+b1). Every PHYS/ROB combination is elaborated separately. The gate runs `read_verilog -sv`, parameter elaboration, `hierarchy -check`, `proc`, `opt`, `memory`, `check -assert`, and rejects black-box modules and inferred `$dlatch` cells. There is no PPA, clock-frequency, area or formal-equivalence threshold. No simulation-only constructs, testbench detection, external files/includes, or verifier manipulation are permitted. All implementation RTL must reside in the three editable source files, kept as ordinary files rather than symlinks.

The verifier simulates only the Yosys-generated netlist in a trusted interface testbench. A separate privileged Python controller independently checks port observations against an instruction-history/ownership ledger; the agent runs as `node`, tool/runtime processes run separately as `nobody`, and only the root verifier can write the reward. Candidate text or success markers cannot establish a pass. Missing or broken toolchain infrastructure is reported separately from candidate synthesis or functional failures. Synthesis has a 180-second limit per configuration; simulator observations have a 30-second resource timeout; the full verifier budget is 1800 seconds. These are execution safety limits, not performance objectives.

Checks include all six finite configurations, exact maximal-prefix admission, arbitrary legal physical allocations, lane bypass, precise commit/recovery, branch boundaries, delayed killed completions, identity wrap under reservations, record compaction under retirement backpressure, and capacity after repeated recovery. The behavioral contract, including late-result lifetime and reset cancellation assumptions, is authoritative.

Shared-tag checks additionally cover ready and pending producers, early/incomplete move acknowledgements, source overwrite, self/zero moves, partial alias retirement, branch recovery, and moves with no free physical capacity when that state is reachable.

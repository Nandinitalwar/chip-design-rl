# Upgrade the legacy rename controller

The three original editable RTL files implement a working **single-inflight, ordinary-instruction** path. `design.sv` holds one pending instruction and the committed map. `map_bypass.sv` reads that map for lane 0. `ownership.sv` selects one unowned tag. Both completion ports and stalled retirement work for this legacy subset.

The requested product supports multiple live instructions, full two-lane prefix admission, speculative mapping, branches/recovery, and move elimination with shared physical tags. Those algorithms are not implemented in the starter. Branches and moves are currently declined, and only lane 0 can be accepted. Complete algorithms are required for the upgraded subsystem.

You may replace or reorganize all logic in the three source files, including helper-module interfaces. Only the top-level `rename_recovery` interface and public behavior are fixed. Simple reconstruction, reference counts, other legal bookkeeping and any legal allocation priority are allowed. Keep the three editable sources as ordinary files and do not depend on external files/includes.

Run the public legacy smoke:

```sh
iverilog -g2012 -s smoke -o /tmp/rename-smoke design.sv map_bypass.sv ownership.sv smoke.sv
vvp /tmp/rename-smoke
```

It resets, accepts a single ordinary writer, completes it on port 1, holds/commits it, and checks a later dependent rename. It does not verify the new multi-record or alias algorithms. Read the full task instruction for the authoritative contract.

A local synthesis check:

```sh
yosys -p 'read_verilog -sv design.sv map_bypass.sv ownership.sv; hierarchy -check -top rename_recovery; proc; opt; memory; opt; check -assert; select -assert-none t:$dlatch'
```

The private gate additionally validates every declared parameter combination, complete interfaces, and alias-aware functional behavior; it accepts unconstrained invalid output bits. Tool acceptance is not a PPA claim.

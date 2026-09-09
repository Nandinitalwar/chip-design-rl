# Rename/recovery repair workspace

Read the task instruction for the complete cycle contract. `design.sv` owns the ordered retirement records and event transitions; `map_bypass.sv` reconstructs mappings and supplies same-bundle sources; `ownership.sv` supplies physical availability and readiness. All are original and editable; the top-level interface is fixed. The implementation may be reorganized across these three files.

Run the public smoke check:

```sh
iverilog -g2012 -s smoke -o /tmp/rename-smoke design.sv map_bypass.sv ownership.sv smoke.sv
vvp /tmp/rename-smoke
```

It checks reset, single allocation, zero sources and an immediately dependent consumer. It is intentionally small, not an exhaustive verifier. The complete contract also requires simultaneous two-lane behavior, checkpoints, completion identity safety and precise retirement/recovery.

For a local synthesis check, run:

```sh
yosys -p 'read_verilog -sv design.sv map_bypass.sv ownership.sv; hierarchy -check -top rename_recovery; proc; opt; memory; opt; check -assert; select -assert-none t:$dlatch'
```

Private grading elaborates all declared parameter configurations and runs independent transactional checks. Synthesis acceptance alone does not establish functional correctness or PPA quality.

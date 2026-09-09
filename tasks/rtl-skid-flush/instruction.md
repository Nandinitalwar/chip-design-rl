Implement `/app/design.sv`: a two-entry registered ready/valid skid queue named `skid_flush`, preserving the supplied module interface and `WIDTH` parameter (default 16, any positive width supported).

This queue sits between a speculative producer and a downstream pipeline stage. Incorrect handling of a flush or a full-queue replacement can leak wrong-path data or drop work.

Required cycle contract:
- `rst` is active high and synchronous. A rising edge with `rst` or `flush` clears all queued words, with priority over transfers.
- While either `rst` or `flush` is asserted, combinational `in_ready` and `out_valid` are zero.
- Otherwise `out_valid` is true exactly when at least one word is queued. `out_data` is the oldest word, stable during stalls. Its value while invalid is unspecified.
- Otherwise `in_ready` is true exactly when fewer than two words are queued OR `out_ready` is true. A full queue supports pop and push on the same edge without a bubble.
- A transfer occurs on a rising edge with valid and ready both true. Simultaneous transfers remove the old front and append input, preserving FIFO order. Accepted input never bypasses directly to output in the same cycle: an empty queue has `out_valid=0` even with input valid.
- There is no obligation for the producer to keep `in_data` stable when `in_valid=0`. No transferred word may be duplicated or lost.

Modify only design.sv. Use synthesizable SystemVerilog; no simulator-specific behavior or testbench detection. Icarus Verilog (`iverilog -g2012`) is available. The deterministic verifier checks reset/flush priority, exact ready/valid behavior, ordering, stalls, capacity, full replacement, and mixed traffic. Reward is 1 only when all checks pass, otherwise 0.

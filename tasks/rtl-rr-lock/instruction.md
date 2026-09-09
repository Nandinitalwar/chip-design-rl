Implement `/app/design.sv`: a round-robin arbiter `rr_lock` for a shared chip interconnect, preserving the interface and parameter `N` (default 4, supported 1 through 8).

The grant is combinational. State changes only on rising clock edges. Every nonzero grant denotes a consumed arbitration slot; there is no separate ready signal.

Required protocol:
- Active-high synchronous `rst` clears ownership and sets the scan pointer to requester 0 on a rising edge. Grant must also be zero combinationally whenever `rst=1`.
- When unlocked, scan requesters from the pointer, wrapping modulo N, and grant exactly the first asserted `req` bit. With no requests grant is zero and pointer stays unchanged.
- At an unlocked rising edge with a winner, if that winner's `lock` bit is 1, capture it as the owner. Otherwise advance the pointer to the index immediately after the winner modulo N.
- While owned, grant the owner exclusively, even when its `req` bit is zero. Ignore every other request and lock bit.
- Ownership ends at a rising edge where the owner's `lock` bit is zero. The cycle immediately BEFORE that release edge still grants the owner. At release, advance the pointer to owner+1 modulo N; subsequent combinational arbitration is unlocked. Do not transfer ownership to another requester on the release edge itself.
- Reset overrides acquisition or release. Ownership persists indefinitely if the owner keeps its lock high; fairness applies to unlocked slots and resumes after release.

Use synthesizable SystemVerilog and modify only design.sv. No simulator-specific behavior or testbench detection. Icarus Verilog (`iverilog -g2012`) is available. Deterministic tests check one-hot grants, cyclic fairness, idle pointer preservation, lock acquisition, owner request withdrawal, release-edge timing, reset, and wraparound, including all supported N=1 through N=8. Reward is 1 only when all checks pass, otherwise 0.

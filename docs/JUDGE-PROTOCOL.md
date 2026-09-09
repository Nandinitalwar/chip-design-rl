# Independent chip-design LLM judge

The judge is an additional engineering review, not the reward oracle and not a human expert certification. The reviewer receives task contracts, starter assets, oracle and grader; evaluation agents receive only the candidate environment and task instructions.

## Review dimensions

Score each dimension from 1 (serious issue) to 5 (strong), with file/behavior evidence and explicit limitations:

1. Engineering realism: credible request for an RTL or kernel engineer.
2. Contract completeness: timing, reset, parameter boundaries, numerical and resource constraints are explicit.
3. Oracle correctness: independent reasoning or counterexample checks support the reference implementation.
4. Grader validity: accepts equivalent correct implementations and rejects meaningful defects.
5. Grader integrity: tests reward actual functionality without implementation-specific or hidden constraints.
6. Difficulty suitability: hypothesis only until model trials establish evidence.

Give an overall verdict: revise, ready for calibration, or insufficient evidence. A high rubric score is not a measured success rate. Track actionable findings with severity, evidence, recommended change and disposition. Root resolves findings; rerun affected checks after changes. Freeze a task revision during its model batch. If a grader defect invalidates runs, preserve them with an invalidation reason and start a new batch under the new hash.

## Attribution after trials

Map each valid failed trial to an observed behavior with evidence, then to a failure-mode taxonomy entry. Keep unknown or ambiguous cases explicit. Intended failure labels must not automatically become observed attribution. Preserve infrastructure failures separately. Use traces only to support observable conclusions, not to claim knowledge of private model reasoning.

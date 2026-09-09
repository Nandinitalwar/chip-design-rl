# Agent swarm

This conversation is the orchestrator. Workers now have separate visible sidebar tasks grouped under Chip-design swarm. This is a status snapshot; trial counts live in trial-results.md.

| Agent | Responsibility | Current status |
|---|---|---|
| Orchestrator (this task) | Delegate work, resolve findings, freeze revisions, integrate and report | Active |
| RTL task author | Build Harbor tasks, oracles, graders and mutation checks | Initial two tasks complete |
| Chip-design expert judge | Independent LLM review of realism, contracts and grader quality | Initial review complete; found two coverage gaps, verified repairs |
| Trial operator | Run isolated Astra trials and report success rates | Running; target ten valid runs per task |
| Requirements researcher | METR/vendor research and reference archive audit | Initial research complete |

## Evidence

- [Expert review](chip-expert-review.md)
- [Trial results](trial-results.md)
- [Machine-readable trial status](trial-summary.json)
- [Living context](CONTEXT.md)
- [Requirements research](market-requirements.md)

The author and judge do not grade their own model attempts. Deterministic graders determine functional rewards; reviewer assessments and measured failure attribution remain separate.

## Visible worker task IDs

- RTL author: 01a087e6-2504-7a13-854f-dde3fcb71cbd
- Expert judge: 01a087e6-2d07-7213-a975-f8756d061e3a
- Trial operator: 01a087e6-3337-7492-8ddc-c7bf9e6ddfbd
- Requirements researcher: 01a087e6-38a3-79e3-9882-b0a70637de55
- Orchestrator: 01a087d9-6366-73d1-88bc-f45e20188cb9

Existing trial processes were handed over without restarting or duplicating them.

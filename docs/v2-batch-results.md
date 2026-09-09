# V2 five-attempt batch: blocked before solving

Frozen task: rtl-rename-recovery-v2. Model: gpt-6-astra/high, fresh Codex tasks with candidate-only containers. Maximum 5 total attempts, then pause.

| Attempt | Outcome | Valid task outcome? |
|---|---|---|
| 1 | Workspace spend cap; no assistant response or tools | No |
| 2 | Workspace spend cap; no assistant response or tools | No |
| 3–5 | Not launched after common blocker identified | No |

**Zero valid trials; no pass-rate estimate.** These errors are infrastructure exclusions, not successful task stumping. Both candidate containers were stopped. No private grading, retries, automatic cap increase or additional launches occurred.

The completed redesign, synthesis/oracle/negative-control validation, independent review and successful Harbor oracle preflight remain valid. They do not establish model difficulty. Exact error/status and worker IDs are retained in v2-batch-results.json and v2-batch-workers.json. This trial configuration differs from earlier Harbor installed-agent runs.

Continuation requires the workspace owner to resolve the spend cap. Three launch slots remain under the current five-total-attempt authorization. Replacing the two invalid launches to obtain five valid outcomes would require explicit additional authorization; no monetary cost is asserted for these blocked requests.

# Buyer acceptance checklist

Prepared 2026-09-09 from the completed [market research](market-requirements.md), [reference review](reference-review.md), [provenance ledger](PROVENANCE.md), and [project context](CONTEXT.md). This document is a delivery review aid, not an acceptance certificate or buyer contract. No additional external research was performed for this checklist; “published” below refers to the primary sources checked in the existing research on 2026-09-09.

The user’s target is **20% per-run failure / 80% per-run success on gpt-6-astra/high**. This is a project target, not a published buyer requirement or an achieved result. Preserve frozen tasks during running trials. Read current results in [trial-results.md](trial-results.md); this checklist does not snapshot or adjudicate an active campaign.

## 1. Verified published guidance, with its actual scope

These are source-backed statements. They do not establish that any organization will buy this package. Checkboxes record whether a delivery review has documented applicability and supporting evidence, not whether the source exists.

| Review check | Published statement and primary source | Scope and acceptance implication |
|---|---|---|
| [ ] Record which historical desiderata apply to the proposed delivery. | METR favors automatically scored tasks, consistent environments, novel solutions, diverse bottlenecks and a spread of difficulty, particularly expert tasks, without incidental confusion. [METR desiderata](https://taskdev.metr.org/desiderata/) | Historical program guidance; no universal 20% failure threshold. Program-specific human duration preferences must not become an invented buyer requirement. |
| [ ] Attach independent human QA evidence, or explicitly mark it missing. | METR describes domain-skilled human testing with comparable resources, time/progress records and issue review, and testing invalid, partial and best solutions. [METR QA](https://taskdev.metr.org/quality-assurance/) | Historical QA guidance. An LLM expert review does not establish independent human completion time or satisfaction of this process. |
| [ ] Supply task, scoring and QA documentation. | METR requests documentation covering evaluation intent, scoring and QA progress/review. [METR documentation](https://taskdev.metr.org/documentation/) | Historical documentation guidance; the buyer must confirm its own required fields and evidence. |
| [ ] Confirm the buyer’s accepted package format. | METR’s Task Standard specifies environment, instructions and optional automatic scoring. [METR Task Standard](https://github.com/METR/task-standard) | A distinct standard. Harbor packaging is the user’s requirement and does not by itself establish METR compatibility. |
| [ ] Keep commercial descriptions consistent with the recorded program status. | METR states its task bounty is paused indefinitely for new ideas, specifications and implementations. [METR suspension notice](https://taskdev.metr.org/suspension/) | Do not describe METR as currently buying tasks or as a confirmed sales channel. Recheck status if a later commercial decision depends on it. |
| [ ] Label other company material as examples rather than procurement terms. | Turing describes a particular verifier-backed environment delivery with repeated rollouts and hard tasks; Mercor describes realistic environments, tools and rigorous verifiers. [Turing case study](https://www.turing.com/case-study/building-production-grade-web-environments-and-verifier-backed-tasks-for-computer-use-agent-rl-training), [Mercor research](https://www.mercor.com/research/) | Published company descriptions, not universal supplier thresholds, contracts or purchase commitments. Turing’s reported difficulty must not replace this project’s target. |

## 2. Project recommendations and user requirements

All items below are proposed delivery gates unless explicitly identified as user requirements. Existing implementation evidence is a starting point; leave the checkbox open until the exact delivery revision and artifacts have been reviewed together.

| Acceptance check | Evidence to include | Current evidence or unresolved work |
|---|---|---|
| [ ] Deliver original, realistic chip-engineering tasks with explicit behavioral contracts. | Interfaces, reset/handshake behavior, parameter ranges, constraints and a concrete engineering objective; domain review. | Original RTL tasks and [task catalog](task-catalog.json); [chip expert review](chip-expert-review.md) is advisory LLM evidence. Human review remains pending. |
| [ ] Deliver the user-required Harbor format and custom harness. | Clean build and run instructions, task configuration, public starter/check path, private verifier and separate oracle; exact dependency versions and image identifiers. | [Harness documentation](harness.md); release dependency/image freezing remains a delivery gate under [provenance](PROVENANCE.md). |
| [ ] Demonstrate deterministic functional grading across the disclosed contract. | Passing oracle, failing starter and targeted incorrect variants, repeatable runs, boundary coverage, and an alternative correct implementation where practical. | [Mutation checker](../tests/check_mutations.py), [validation record](validation.json), and [expert review](chip-expert-review.md). The context records passing expanded oracle checks and ten negative controls; confirm these against the delivered revision. |
| [ ] Review grading integrity independently of functional coverage. | Agent image excludes hidden tests/oracle; trusted grading cannot be changed by the candidate; executable candidate code cannot forge acceptance artifacts. | [Reference review](reference-review.md) identifies a simulator/system-task attack surface in the supplied archive, not a reproduced exploit in these tasks. Do not claim current-package security from functional tests alone. |
| [ ] Measure the user’s 20% failure target on gpt-6-astra/high. | Exact task hash, model identifier, effort, harness/runtime, budgets, isolation/reset policy, all outcomes, valid-run denominator and confidence interval. | [Calibration protocol](CALIBRATION.md) and [live trial results](trial-results.md). The underlying difficulty remains unverified until reviewed trial evidence supports the agreed criterion. Ten trials are screening, not proof of a precise population failure rate. |
| [ ] Preserve evaluation independence and the complete outcome record. | Frozen task revision within a campaign; authors excluded as calibration candidates; no context from prior attempts; separate infrastructure outcomes; independent validation after revisions. | Project policy in [context](CONTEXT.md). Do not edit tasks during running trials, silently omit failed runs, or count infrastructure failures as model failures. |
| [ ] Report observed failure mechanisms separately from intended mechanisms. | Trace/test references supporting each attribution; primary/secondary labels and uncertainty. | [Failure-mode metadata](failure-modes.md); intended mechanisms remain hypotheses until supported by trial evidence. |
| [ ] Complete independent human QA. | Domain expert identity/qualification as permitted, comparable resources, elapsed time, assistance, issue log and resolution. | Not established by initial research, model trials or the independent LLM judge. |
| [ ] State supported engineering claims precisely. | Functional simulation evidence; synthesis, timing, area or performance evidence only when actually measured with declared tooling/hardware. | Current RTL scope is functional pilot calibration. Synthesis is unverified. [NKI backlog](NKI-BACKLOG.md) requires target hardware before Trainium performance claims. |
| [ ] Provide operational reproducibility and cost records. | Build/run resources, pinned dependencies, seed policy, timeouts, reset/cleanup, infrastructure failure handling and measured run costs. | [Harness](harness.md) and [calibration](CALIBRATION.md) provide starting documentation; verify delivery completeness and measured costs. |
| [ ] Complete provenance and distribution review for every delivered asset. | Origins of starter code, tests, oracle, docs, dependencies, images and traces; applicable notices and authorized rights/terms. | [Provenance ledger](PROVENANCE.md) is not ownership clearance. User ZIP remains reference-only; do not redistribute its assets or source with unknown rights. No open-source/commercial license has been granted by initialization. |
| [ ] Protect solutions and any agreed held-out evaluation material. | Private storage and access policy, separate delivery boundaries, development versus holdout inventory, permitted trace retention/use. | Private assets are the default. A holdout policy and buyer-approved disclosure boundaries still need explicit delivery evidence. |

### Calibration language for a delivery report

Use `successes / valid_runs` and `failures / valid_runs`; report infrastructure attempts separately and preserve their records. Do not call the per-run fraction `pass@10`. For example, 8 successes in 10 valid runs gives 80% observed success and an approximate 95% Wilson success interval of 49.0–94.3%; it does not certify a stable 20% underlying failure rate. This example is explanatory, not a result from the running campaign. The buyer must specify the acceptable band, sample size and decision rule before it can serve as a contractual gate.

## 3. Buyer-specific unanswered items

No buyer has been identified and no contract, pricing or purchase commitment has been established. These are questions to resolve with an authorized buyer process; they are not instructions to contact anyone.

| Open item | Answer required before acceptance can be claimed |
|---|---|
| [ ] Buyer and use case | Who accepts the work, and is it for RL training, evaluation, research or another permitted use? |
| [ ] Domain and volume | RTL versus NKI mix, task count, breadth, novelty expectations and delivery schedule. |
| [ ] Package and execution | Harbor version/schema or another required format; supported OS, container runtime, hardware, network access and tool policies. |
| [ ] Difficulty decision | Model/version and effort, budgets, acceptable failure band around the user’s target, sample size, statistical rule, and handling of infrastructure errors and model updates. |
| [ ] Verifier acceptance | Reward schema, determinism tolerance, permitted equivalent solutions, required negative controls, adversarial review and dispute/regrade process. |
| [ ] Engineering depth | Whether functional simulation suffices or synthesis, PPA, hardware performance or independent human benchmarking is mandatory. |
| [ ] Rights and confidentiality | Training/evaluation rights, ownership or licensing, exclusivity, redistribution, dependency obligations, trace use, retention and solution disclosure. |
| [ ] Data and evidence | Required metadata, trajectories, human QA records, review qualifications, privacy handling and contamination/holdout policy. |
| [ ] Commercial terms | Price, payment milestones, acceptance window, rejection/remediation rules, support and maintenance expectations. |

Completion of the project gates supports a reviewable package. Only the actual buyer’s agreed criteria and acceptance process can establish buyer acceptance.

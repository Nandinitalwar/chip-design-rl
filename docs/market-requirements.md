# RL task supply: evidence and project acceptance criteria

> Target correction: the latest user instruction is **20% pass / 80% failure**. Earlier target statements below are historical. Existing frozen trials are unchanged; new candidate selection uses the corrected target.
Research checked 2026-09-09. This is technical market research, not a buyer contract or confirmation of commercial acceptance.

## The difficulty target needs explicit naming

The user has confirmed **20% failure**, equivalent to **80% per-run success**, or about **8 successes in 10 independent runs**. This supersedes the supplied example's **1–2 successful attempts in 10**. Do not report the target as achieved before repeated, isolated Astra evaluations. A harder profile may remain configurable, but is not the acceptance target.

No universal requirement to sell tasks at a 20% failure rate was found in the official sources reviewed. METR's historical task guide instead seeks a spread of difficulty, especially expert tasks, without incidental confusion; it favors automatic scoring, consistent environments, novel solutions, diverse bottlenecks, and generally one major hard step. Its preferred human duration is specific to that evaluation program, not an industry procurement rule. [METR desiderata](https://taskdev.metr.org/desiderata/)

Turing describes one commercial delivery where hard tasks had fewer than two successful attempts in ten, alongside realistic environments, verifiers, and repeated rollouts. This supports demand for a hard tier, but is neither a universal seller threshold nor evidence of an active purchasing offer. That page labels the count “Pass@10”; here use `successes / valid_runs` to avoid confusion with the conventional probability of at least one success in ten. [Turing case study](https://www.turing.com/case-study/building-production-grade-web-environments-and-verifier-backed-tasks-for-computer-use-agent-rl-training)

For independent trials with per-run success probability p, probability of at least one success in ten is 1−(1−p)^10. Thus 20% per-run success implies about 89% chance of at least one success across ten attempts, not 20% pass@10. Ten trials are an initial screen: 2/10 has an approximate 95% Wilson interval of 5.7–51.0%, and 8/10 of 49.0–94.3%. A count alone cannot certify a stable 20% population rate.

## What METR actually offers

METR's published task bounty is **paused indefinitely for new ideas, specifications, and implementations**. Do not represent METR as an open sales channel. [Official suspension notice](https://taskdev.metr.org/suspension/)

Its technical guidance remains useful. An independent domain-skilled human should try the task using comparable resources, record time/progress and review issues; its alternatives include testing invalid, partial, and best solutions. This is historical QA guidance, not proof these tasks have passed it. [METR QA](https://taskdev.metr.org/quality-assurance/)

METR requests task and QA documentation, including what is evaluated, how scoring works, progress, and review evidence. [METR documentation](https://taskdev.metr.org/documentation/) Its Task Standard describes environment, instructions, and optional automatic scoring; it is distinct from the user's requested Harbor packaging. [METR Task Standard](https://github.com/METR/task-standard)

Mercor's own research page emphasizes realistic worlds, usable tools, rigorous tasks and verifiers. It does not publish a universal rejection-rate threshold or vendor acceptance contract. [Mercor research](https://www.mercor.com/research/)

## Proposed delivery requirements for this project

The following are project recommendations inferred from the sources and the user's request, not quoted purchasing terms:

| Deliverable | Acceptance evidence |
|---|---|
| Real chip engineering task | Concrete defect or design request, declared interfaces and constraints; domain review |
| Harbor package | Clean environment build, prompt, task config, isolated tests, separate oracle |
| Correct deterministic reward | Oracle passes; baseline and discriminating incorrect variants fail; equivalent valid implementation accepted |
| Grader integrity | No hidden constraints; reset between trials; trusted evaluation separated from agent edits; no solution in agent image |
| Difficulty evidence | Exact model/version and effort, harness, budgets, task hash, all run outcomes, confidence interval |
| Failure analysis | Primary and secondary hypotheses per task; observed attribution supported by test IDs and traces |
| Human QA | Independent expert time, findings, fixes, and assistance disclosed |
| Operational data | Build/run costs, resource needs, repeatability, failure handling, seed policy |
| Provenance record | Origin and redistribution status of code, docs, tests, solutions and collected traces; buyer-specific terms remain unresolved |
| Evaluation integrity | Separate development and holdout variants; private solutions and held-out tests |

Before claiming a sellable dataset, obtain the actual buyer's required format, rights terms, domain mix, volume, difficulty band, and acceptance process. No price or purchase commitment has been established. Hardware kernel tasks additionally need an actual target-hardware validation path; a CPU simulator cannot substantiate Trainium performance claims.

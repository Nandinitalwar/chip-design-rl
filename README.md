# Chip-design RL tasks

Private development repository for realistic chip-design tasks targeting **20% pass on GPT-6 Astra** (about 2/10 independent successes). Difficulty is **not yet calibrated**. The target was corrected by the user; existing simple-task campaigns began under an earlier 80% pass target and remain separate evidence.

Three original Harbor tasks and a custom Python harness are included:

| Task | Engineering behavior | Intended failure modes |
|---|---|---|
| `rtl-skid-flush` | Two-entry registered ready/valid queue | Flush priority, full replacement, FIFO ordering |
| `rtl-rr-lock` | Round-robin interconnect arbitration with ownership | Lock persistence, release-edge timing, pointer fairness |
| `rtl-rename-recovery` | Two-wide rename, register ownership, retirement and branch recovery | Commit/recovery ordering, stale completions, checkpoint reclamation |

All have explicit contracts, starter RTL, separate oracles and deterministic graders. Native oracles pass, starters fail, and ten semantic mutants are rejected. These results establish test discrimination, not the target model's success rate. The initial two tasks have simulation-only grading. Rename recovery additionally checks synthesis and generated-netlist behavior with a privileged external grader. Its oracle passed Harbor preflight; three legitimate variants and thirteen negative controls passed the acceptance/rejection checks. It has no model trials yet.

## Use

Requires Python 3.11+, Icarus Verilog (`iverilog`, `vvp`), and GNU `timeout` (or `gtimeout` on macOS). Model/container execution additionally requires Harbor 0.22.0 and a working Docker daemon.

```sh
python -m unittest discover -s tests -v
python tests/check_mutations.py
python -m harness.cli validate tasks/*
python -m harness.cli oracle tasks/rtl-skid-flush tasks/rtl-rr-lock --out runs/oracle
python -m harness.cli baseline tasks/rtl-skid-flush tasks/rtl-rr-lock --out runs/baseline
python -m harness.cli trials tasks/* --trials 10 --effort high
```

The last command prints a plan. Add `--execute` to run it with configured Codex authentication. The standard Harbor adapter supports `CODEX_FORCE_AUTH_JSON=1` for local Codex sign-in. Credentials and raw runs must not be committed. See [harness documentation](docs/harness.md) for result handling and limitations.

## Project record

- [Living instructions and status](docs/CONTEXT.md)
- [Requirements and METR research](docs/market-requirements.md)
- [Calibration protocol](docs/CALIBRATION.md)
- [Failure-mode taxonomy and attribution](docs/failure-modes.md)
- [Independent chip-design LLM review](docs/chip-expert-review.md)
- [Trial results](docs/trial-results.md)
- [Static review of supplied example](docs/reference-review.md)
- [Provenance ledger](docs/PROVENANCE.md)
- [NKI candidate backlog](docs/NKI-BACKLOG.md)

METR's public task bounty is paused; no universal selling requirement for 20% failure was found. Buyer-specific acceptance terms, expert review, dependency freezing and independent calibration remain release prerequisites. The user archive is not redistributed here.

Rename recovery requires Docker/root verifier isolation; use `harbor run -p tasks/rtl-rename-recovery -a oracle -n 1` for its oracle check, rather than the native convenience runner. See [final author validation](docs/rename-recovery-validation.md) and [freeze record](docs/rename-freeze.json).

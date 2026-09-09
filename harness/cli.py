"""Python 3.11+ stdlib harness. Run with python -m harness.cli --help."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import uuid
from functools import lru_cache

MODEL = "gpt-6-astra"
STATUSES = {"success", "model_failure", "infra_error"}


def task_hash(task):
    digest = hashlib.sha256()
    for path in sorted(task.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Task symlink is unsupported: {path}")
        if path.is_file():
            name = path.relative_to(task).as_posix().encode()
            data = path.read_bytes()
            digest.update(len(name).to_bytes(8, "big") + name)
            digest.update(len(data).to_bytes(8, "big") + data)
    return digest.hexdigest()


def validate(task):
    required = ["instruction.md", "task.toml", "environment/Dockerfile",
                "solution/solve.sh", "tests/test.sh"]
    errors = [f"Missing {name}" for name in required if not (task / name).is_file()]
    if errors:
        return errors
    try:
        config = tomllib.loads((task / "task.toml").read_text())
        for section in ("metadata", "verifier", "agent", "environment"):
            if not isinstance(config.get(section), dict):
                errors.append(f"Missing configuration section [{section}]")
        if not (task / "environment/repo").is_dir():
            errors.append("Native harness requires environment/repo")
        task_hash(task)
    except (ValueError, OSError) as exc:
        errors.append(str(exc))
    return errors


def wilson(successes, count, z=1.959963984540054):
    if count < 0 or not 0 <= successes <= count:
        raise ValueError("Invalid binomial counts")
    if count == 0:
        return None
    p = successes / count
    denom = 1 + z*z/count
    center = (p + z*z/(2*count))/denom
    half = z*math.sqrt(p*(1-p)/count + z*z/(4*count*count))/denom
    return [max(0.0, center-half), min(1.0, center+half)]


def aggregate(records):
    """Refuse mixed configurations and duplicate trials; exclude infrastructure errors."""
    seen, groups = set(), {}
    for record in records:
        if record.get("status") not in STATUSES:
            raise ValueError("Unrecognized trial status")
        trial_id = record["trial_id"]
        if trial_id in seen:
            raise ValueError(f"Duplicate trial {trial_id}")
        seen.add(trial_id)
        key = tuple(record[k] for k in ("task", "task_hash", "model", "effort", "kind"))
        groups.setdefault(key, []).append(record)
    output = []
    for key, items in sorted(groups.items()):
        counts = Counter(r["status"] for r in items)
        n = counts["success"] + counts["model_failure"]
        output.append(dict(zip(("task", "task_hash", "model", "effort", "kind"), key)) | {
            "attempts": len(items), "valid_trials": n, "successes": counts["success"],
            "failures": counts["model_failure"], "infra_errors": counts["infra_error"],
            "success_rate": counts["success"]/n if n else None,
            "failure_rate": counts["model_failure"]/n if n else None,
            "success_wilson_95": wilson(counts["success"], n),
            "failure_wilson_95": wilson(counts["model_failure"], n)})
    return output


def binary_reward(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or value not in (0, 1):
        raise ValueError("Expected a finite binary reward (0 or 1)")
    return "success" if value == 1 else "model_failure"


def classify_harbor(result):
    """Conservatively quarantine all Harbor exceptions for manual adjudication."""
    if result.get("exception_info"):
        return "infra_error", "Harbor exception; review exception_info before attribution"
    try:
        reward = result["verifier_result"]["rewards"]["reward"]
        return binary_reward(reward), None
    except (KeyError, TypeError, ValueError):
        return "infra_error", "Missing or invalid binary verifier reward"


def base_record(task, kind, effort="n/a"):
    return {"schema_version": 1, "trial_id": str(uuid.uuid4()), "task": task.name,
            "task_hash": task_hash(task), "model": MODEL if kind == "model" else "none",
            "effort": effort, "kind": kind,
            "started_at": datetime.now(timezone.utc).isoformat()}


def save_record(record, out):
    out.mkdir(parents=True, exist_ok=True)
    (out / f'{record["trial_id"]}.json').write_text(json.dumps(record, indent=2) + "\n")


def native(task, kind, out, timeout=120):
    record = base_record(task, kind)
    record.update(status="infra_error", reason=None)
    missing = [tool for tool in ("bash", "iverilog", "vvp") if not shutil.which(tool)]
    if missing:
        record["reason"] = "Missing executables: " + ", ".join(missing)
        save_record(record, out)
        return record
    try:
        with tempfile.TemporaryDirectory(prefix="chip-rtl-") as temp:
            workspace = Path(temp) / "repo"
            shutil.copytree(task / "environment/repo", workspace)
            logs = Path(temp) / "verifier"
            logs.mkdir()
            env = os.environ | {"TASK_WORKSPACE": str(workspace), "VERIFIER_LOG_DIR": str(logs)}
            phases = ["solution/solve.sh", "tests/test.sh"] if kind == "oracle" else ["tests/test.sh"]
            for phase in phases:
                process = subprocess.run(["bash", str(task / phase)], cwd=workspace,
                                         env=env, capture_output=True, text=True, timeout=timeout)
                record.setdefault("phases", []).append({"phase": phase, "returncode": process.returncode,
                                                        "stdout": process.stdout, "stderr": process.stderr})
                if process.returncode:
                    raise RuntimeError(f"{phase} exited {process.returncode}; infrastructure or script error")
            reward = float((logs / "reward.txt").read_text().strip())
            record["status"] = binary_reward(reward)
            record["reward"] = reward
            record["verifier_files"] = {p.name: p.read_text(errors="replace") for p in logs.iterdir() if p.is_file() and p.suffix in (".log", ".txt", ".json")}
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        record["reason"] = str(exc)
    save_record(record, out)
    return record


def harbor_command(task, job_root, trial_id, effort):
    return ["harbor", "run", "-p", str(task), "-a", "codex", "-m", MODEL,
            "--agent-kwarg", f"reasoning_effort={effort}", "--n-attempts", "1",
            "--n-concurrent", "1", "--max-retries", "0", "--job-name", trial_id,
            "--jobs-dir", str(job_root)]


@lru_cache(maxsize=1)
def runner_versions():
    versions = {}
    for tool in ("harbor", "docker", "codex"):
        try:
            proc = subprocess.run([tool, "--version"], capture_output=True, text=True, timeout=10)
            versions[tool] = proc.stdout.strip() if proc.returncode == 0 else "unavailable"
        except (OSError, subprocess.TimeoutExpired):
            versions[tool] = "unavailable"
    return versions


def run_model(task, out, effort, timeout):
    record = base_record(task, "model", effort)
    command = harbor_command(task, out / "jobs", record["trial_id"], effort)
    record.update(command=command, status="infra_error", reason=None, host_tool_versions=runner_versions())
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        record.update(returncode=process.returncode, stdout=process.stdout, stderr=process.stderr)
        if process.returncode:
            raise RuntimeError(f"Harbor exited {process.returncode}")
        results = list((out / "jobs" / record["trial_id"]).glob("*/result.json"))
        if len(results) != 1:
            raise ValueError(f"Expected one trial result, found {len(results)}")
        result = json.loads(results[0].read_text())
        record["harbor_result"] = str(results[0])
        record["status"], record["reason"] = classify_harbor(result)
        model_info = (result.get("agent_info") or {}).get("model_info") or {}
        record["reported_model"] = model_info.get("name")
        if record["reported_model"] != MODEL:
            record.update(status="infra_error", reason="Reported model differs from requested gpt-6-astra")
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        record["reason"] = str(exc)
    save_record(record, out)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "oracle", "baseline", "trials"):
        p = sub.add_parser(command)
        p.add_argument("tasks", nargs="+", type=Path)
        if command != "validate":
            p.add_argument("--out", type=Path, default=Path("runs"))
            p.add_argument("--timeout", type=int, default=3600 if command == "trials" else 120)
        if command == "trials":
            p.add_argument("--trials", type=int, default=10)
            p.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max", "ultra"], default="high")
            p.add_argument("--target-success", type=float, default=0.8)
            p.add_argument("--profile", choices=["original", "hard"], default="original")
            p.add_argument("--execute", action="store_true", help="Actually launch trials; default prints a plan")
    sub.add_parser("report").add_argument("records", nargs="+", type=Path)
    args = parser.parse_args()
    if args.command == "report":
        records = [json.loads(p.read_text()) for p in args.records]
        print(json.dumps(aggregate(records), indent=2))
        return 0
    if args.command == "trials" and (args.trials < 1 or not 0 <= args.target_success <= 1):
        parser.error("trials must be positive and target success in [0, 1]")
    if args.command != "validate":
        args.out = args.out.resolve()
        if args.timeout <= 0:
            parser.error("timeout must be positive")
    failed = False
    for supplied in args.tasks:
        task = supplied.resolve()
        errors = validate(task)
        if errors:
            print(json.dumps({"task": str(task), "errors": errors}))
            failed = True
            continue
        if args.command == "validate":
            print(json.dumps({"task": str(task), "valid": True, "task_hash": task_hash(task)}))
        elif args.command in ("oracle", "baseline"):
            result = native(task, args.command, args.out, args.timeout)
            print(json.dumps({k: result.get(k) for k in ("trial_id", "task", "kind", "status", "reason")}))
            expected = "success" if args.command == "oracle" else "model_failure"
            failed |= result["status"] != expected
        elif not args.execute:
            plan = {"task": task.name, "task_hash": task_hash(task), "model": MODEL, "effort": args.effort,
                    "trials": args.trials, "target_success": [0.1, 0.2] if args.profile == "hard" else args.target_success,
                    "measured": False,
                    "commands": [harbor_command(task, args.out / "jobs", str(uuid.uuid4()), args.effort)
                                 for _ in range(args.trials)]}
            print(json.dumps(plan, indent=2))
        else:
            for _ in range(args.trials):
                result = run_model(task, args.out, args.effort, args.timeout)
                print(json.dumps({k: result.get(k) for k in ("trial_id", "task", "kind", "status", "reason")}))
                if result["status"] == "infra_error":
                    failed = True
                    break  # Fix infrastructure before spending more trial attempts.
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from harness.cli import aggregate, binary_reward, classify_harbor, harbor_command, native, wilson


class HarnessTests(unittest.TestCase):
    def record(self, status, trial_id="1", **changes):
        return dict(trial_id=trial_id, task="task", task_hash="abc", model="gpt-6-astra",
                    effort="high", kind="model", status=status) | changes

    def test_wilson(self):
        lo, hi = wilson(8, 10)
        self.assertAlmostEqual(lo, 0.4901624715)
        self.assertAlmostEqual(hi, 0.9433178485)
        self.assertIsNone(wilson(0, 0))
        self.assertAlmostEqual(wilson(0, 10)[0], 0)
        self.assertAlmostEqual(wilson(10, 10)[1], 1)
        with self.assertRaises(ValueError):
            wilson(11, 10)

    def test_infrastructure_excluded(self):
        records = [self.record("success"), self.record("model_failure", "2"), self.record("infra_error", "3")]
        result = aggregate(records)[0]
        self.assertEqual(result["valid_trials"], 2)
        self.assertEqual(result["failure_rate"], .5)
        self.assertEqual(result["infra_errors"], 1)
        self.assertIsNone(aggregate([self.record("infra_error")])[0]["failure_rate"])

    def test_duplicates_and_unknown_status_rejected(self):
        with self.assertRaises(ValueError):
            aggregate([self.record("success"), self.record("success")])
        with self.assertRaises(ValueError):
            aggregate([self.record("timeout")])

    def test_separates_effort_and_task_versions(self):
        records = [self.record("success"), self.record("model_failure", "2", effort="low"),
                   self.record("success", "3", task_hash="different")]
        self.assertEqual(len(aggregate(records)), 3)

    def test_harbor_classification(self):
        self.assertEqual(classify_harbor({"verifier_result": {"rewards": {"reward": 0}}})[0], "model_failure")
        self.assertEqual(classify_harbor({"verifier_result": {"rewards": {"reward": 1}}})[0], "success")
        for bad in ({}, {"exception_info": {"exception_type": "Timeout"}, "verifier_result": {"rewards": {"reward": 0}}},
                    {"verifier_result": {"rewards": {"reward": .5}}}):
            self.assertEqual(classify_harbor(bad)[0], "infra_error")
        for bad in (float("nan"), float("inf"), True, "1", .5):
            with self.assertRaises(ValueError):
                binary_reward(bad)

    def test_command_has_no_retries_or_oracle(self):
        command = harbor_command(Path("/tmp/a b"), Path("/tmp/jobs"), "trial", "high")
        self.assertIn("/tmp/a b", command)
        self.assertIn("gpt-6-astra", command)
        self.assertEqual(command[command.index("--max-retries")+1], "0")
        self.assertNotIn("oracle", command)

    def test_missing_tool_recorded_as_infrastructure(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp) / "task"
            task.mkdir()
            out = Path(tmp) / "results"
            with patch("harness.cli.shutil.which", return_value=None):
                result = native(task, "oracle", out)
            self.assertEqual(result["status"], "infra_error")
            self.assertIn("iverilog", result["reason"])
            self.assertEqual(json.loads(next(out.glob("*.json")).read_text())["status"], "infra_error")

    def test_native_isolated_oracle_and_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = Path(tmp) / "task"
            for directory in ("environment/repo", "solution", "tests"):
                (task / directory).mkdir(parents=True)
            (task / "environment/repo/design").write_text("broken")
            (task / "solution/solve.sh").write_text('printf fixed > "$TASK_WORKSPACE/design"\n')
            (task / "tests/test.sh").write_text('if [ "$(cat "$TASK_WORKSPACE/design")" = fixed ]; then r=1; else r=0; fi\nprintf "%s" "$r" > "$VERIFIER_LOG_DIR/reward.txt"\n')
            with patch("harness.cli.shutil.which", return_value="present"):
                oracle = native(task, "oracle", Path(tmp)/"results")
                baseline = native(task, "baseline", Path(tmp)/"results")
            self.assertEqual(oracle["status"], "success")
            self.assertEqual(baseline["status"], "model_failure")
            self.assertEqual((task / "environment/repo/design").read_text(), "broken")


if __name__ == "__main__":
    unittest.main()

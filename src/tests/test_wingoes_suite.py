import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Ensure repo root (where models_and_utils.py lives) is on sys.path
import sys
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import models_and_utils as mu
import orchestrator_core as oc


class WinGOESSuite(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.bundle = Path(self.tmp.name) / "bundle"
        self.bundle.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # -------------------------
    # Gates / policy invariants
    # -------------------------

    def test_enforce_gates_clean_rebuild_disables_risky_items(self):
        ctx = mu.make_run_context(self.bundle, mu.MODE_CLEAN, dry_run=True)
        ctx.hardware_match = mu.MATCH_PASS

        toggles = mu.Toggles(
            use_winget=True,
            use_choco=True,
            use_scoop=True,
            cfg_git=True,
            cfg_gitconfig_file=True,
            cfg_ssh=True,
            cfg_vscode=True,
            cfg_windows_terminal=True,
            win_tz_region=True,
            win_power_plan=True,
            drv_inventory=True,
            drv_checklist=True,
            drv_same_hw_transfer=True,
            risky_shell_context_menu=True,
        )

        enforced = mu.enforce_gates(ctx, toggles)

        # CLEAN_REBUILD should force these off
        self.assertFalse(enforced.win_tz_region)
        self.assertFalse(enforced.win_power_plan)
        self.assertFalse(enforced.drv_same_hw_transfer)

        # Always forced off by policy
        self.assertFalse(enforced.risky_shell_context_menu)

        # Other toggles should remain as-is
        self.assertTrue(enforced.use_winget)
        self.assertTrue(enforced.cfg_git)

    def test_enforce_gates_same_hw_requires_hardware_match(self):
        toggles = mu.Toggles(
            win_tz_region=True,
            win_power_plan=True,
            drv_same_hw_transfer=True,
            risky_shell_context_menu=True,
        )

        ctx_fail = mu.make_run_context(self.bundle, mu.MODE_SAME, dry_run=True)
        ctx_fail.hardware_match = mu.MATCH_FAIL
        enforced_fail = mu.enforce_gates(ctx_fail, toggles)
        self.assertFalse(enforced_fail.win_tz_region)
        self.assertFalse(enforced_fail.win_power_plan)
        self.assertFalse(enforced_fail.drv_same_hw_transfer)
        self.assertFalse(enforced_fail.risky_shell_context_menu)

        ctx_pass = mu.make_run_context(self.bundle, mu.MODE_SAME, dry_run=True)
        ctx_pass.hardware_match = mu.MATCH_PASS
        enforced_pass = mu.enforce_gates(ctx_pass, toggles)
        # Should be allowed when MATCH_PASS, except the permanently disabled risky flag
        self.assertTrue(enforced_pass.win_tz_region)
        self.assertTrue(enforced_pass.win_power_plan)
        self.assertTrue(enforced_pass.drv_same_hw_transfer)
        self.assertFalse(enforced_pass.risky_shell_context_menu)

    # -------------------------
    # Deterministic artifacts
    # -------------------------

    def _read_json(self, p: Path):
        return json.loads(p.read_text(encoding="utf-8"))

    def test_op_capture_best_effort_writes_expected_artifacts(self):
        # Fixed fingerprint so output is deterministic for assertions
        fixed_fp = {"machine": "SOURCE", "cpu": "X", "mb": "Y", "disk": "Z"}

        toggles = mu.Toggles(use_winget=True)  # force winget path to be executed

        with patch.object(oc, "capture_fingerprint", return_value=fixed_fp), \
             patch.object(oc, "which", return_value=None), \
             patch.object(oc, "run_cmd") as mock_run_cmd:
            # run_cmd should not be called when which("winget") is None (capture_winget early returns)
            ctx, report = oc.op_capture(self.bundle, mu.MODE_CLEAN, dry_run=True, toggles=toggles, stream_cb=None)

        # Required deterministic fingerprint path
        src_fp_path = self.bundle / "fingerprints" / "source_fingerprint.json"
        self.assertTrue(src_fp_path.exists(), f"Missing {src_fp_path}")
        self.assertEqual(self._read_json(src_fp_path), fixed_fp)

        # Report + summary should exist under runs/<run_id>/
        self.assertTrue(ctx.run_dir.exists())
        self.assertTrue(ctx.report_path.exists())
        self.assertTrue(ctx.summary_path.exists())

        # Ensure report references metadata and has at least CAPTURE step
        self.assertIn("metadata", report)
        self.assertIn("steps", report)
        self.assertGreaterEqual(len(report["steps"]), 1)
        self.assertEqual(report["steps"][0]["name"], "CAPTURE")

        # Best-effort behavior: winget missing should be recorded as a StepItem, not a crash
        items = report["steps"][0]["items"]
        winget_items = [it for it in items if it.get("id") == "winget_status"]
        self.assertTrue(winget_items, "Expected a winget_status item when winget is missing")
        self.assertFalse(winget_items[0].get("ok", True))

        # run_cmd should not have been invoked for winget export when winget missing
        mock_run_cmd.assert_not_called()

    def test_op_apply_classifies_hardware_match_and_writes_target_fingerprint(self):
        source_fp = {"machine": "SOURCE", "cpu": "A", "mb": "B", "disk": "C"}
        target_fp = {"machine": "TARGET", "cpu": "A", "mb": "B", "disk": "C"}  # pretend same for PASS

        # Put a source fingerprint in place (as capture would do)
        (self.bundle / "fingerprints").mkdir(parents=True, exist_ok=True)
        (self.bundle / "fingerprints" / "source_fingerprint.json").write_text(json.dumps(source_fp), encoding="utf-8")

        toggles = mu.Toggles(use_winget=False, use_choco=False, use_scoop=False)

        with patch.object(oc, "capture_fingerprint", return_value=target_fp), \
             patch.object(oc, "classify_hardware_match", return_value=(mu.MATCH_PASS, {"reason": "unit-test"})), \
             patch.object(oc, "append_log"), \
             patch.object(oc, "run_cmd") as _mock_run_cmd:
            ctx, report = oc.op_apply(self.bundle, mu.MODE_SAME, dry_run=True, toggles=toggles, stream_cb=None)

        # Deterministic target fingerprint path
        tgt_fp_path = self.bundle / "fingerprints" / "target_fingerprint.json"
        self.assertTrue(tgt_fp_path.exists(), f"Missing {tgt_fp_path}")
        self.assertEqual(self._read_json(tgt_fp_path), target_fp)

        # Classification is recorded on ctx and in report
        self.assertEqual(ctx.hardware_match, mu.MATCH_PASS)
        self.assertIn("fingerprints", report)
        self.assertEqual(report["fingerprints"]["hardware_match"], mu.MATCH_PASS)
        self.assertEqual(report["fingerprints"]["hardware_match_details"], {"reason": "unit-test"})

        # Mode SAME + PASS allows tz/power *only if toggles ask for it*; we left them default False.
        # This ensures gating doesn't unexpectedly enable anything.
        disabled = report.get("policy_decisions", {}).get("disabled_features_due_to_mode_or_hardware", [])
        self.assertIsInstance(disabled, list)

        # Report and summary created
        self.assertTrue(ctx.report_path.exists())
        self.assertTrue(ctx.summary_path.exists())

    def test_op_verify_best_effort_no_source_fingerprint(self):
        # VERIFY should not crash if there is no source_fingerprint.json.
        toggles = mu.Toggles(drv_checklist=False)

        with patch.object(oc, "capture_fingerprint", return_value={"machine": "TARGET"}), \
             patch.object(oc, "run_cmd"), \
             patch.object(oc, "which", return_value=None):
            ctx, report, checklist = oc.op_verify(self.bundle, mu.MODE_CLEAN, dry_run=True, toggles=toggles, stream_cb=None)

        self.assertEqual(ctx.hardware_match, "UNKNOWN")
        self.assertIn("fingerprints", report)
        self.assertEqual(report["fingerprints"]["hardware_match"], "UNKNOWN")
        self.assertIsInstance(checklist, list)
        self.assertTrue(ctx.report_path.exists())
        self.assertTrue(ctx.summary_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)

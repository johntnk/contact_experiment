from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deepskin_data.manifest import build_gold_manifest
from deepskin_data.recorder import finalize_metadata, summarize_trial, validate_trial_directory, write_trial_atomic
from deepskin_data.schema import TrialMetadata

ORDER_SCRIPT = REPO_ROOT / "scripts" / "generate_session_order.py"
spec = importlib.util.spec_from_file_location("generate_session_order", ORDER_SCRIPT)
order_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(order_module)

SESSION_SCRIPT = REPO_ROOT / "scripts" / "record_session.py"
session_spec = importlib.util.spec_from_file_location("record_session", SESSION_SCRIPT)
session_module = importlib.util.module_from_spec(session_spec)
assert session_spec.loader is not None
session_spec.loader.exec_module(session_module)


def arrays() -> dict[str, np.ndarray]:
    return {
        "matrix": np.arange(24, dtype=np.float64).reshape(4, 2, 3),
        "timestamps_ms": np.asarray([0.0, 20.0, 40.0, 60.0]),
        "frame_ids": np.arange(4, dtype=np.int64),
        "touch_state": np.asarray([False, True, True, False]),
    }


def metadata(status: str = "VALID") -> TrialMetadata:
    valid = status == "VALID"
    return TrialMetadata(
        operator_id="operator_01",
        session_id="session_01",
        trial_id="trial_000001",
        instruction_label="STROKE",
        verified_label="STROKE" if valid else None,
        trial_status=status,
        label_source="CONTROLLED_CONFIRMED" if valid else None,
        label_quality="GOLD" if valid else None,
        intensity_instruction="NORMAL",
        speed_instruction="SLOW",
        direction_instruction="LEFT_TO_RIGHT",
        position_instruction="CENTER",
        contact_style_instruction=None,
        pulse_count_instruction=None,
        device_model="fake",
        matrix_rows=2,
        matrix_cols=3,
        sampling_rate_observed_hz=50.0,
        recorded_at="2026-08-20T00:00:00+08:00",
        frame_count=4,
        duration_ms=60.0,
        host_poll_rate_hz=60.0,
    )


class TrialDataTests(unittest.TestCase):
    def test_valid_requires_explicit_verified_label(self):
        invalid = metadata().__class__(**{**metadata().to_dict(), "verified_label": None})
        with self.assertRaisesRegex(ValueError, "explicit"):
            invalid.validate()

    def test_valid_rejects_label_different_from_instruction(self):
        invalid = metadata().__class__(**{**metadata().to_dict(), "verified_label": "TAP"})
        with self.assertRaisesRegex(ValueError, "match instruction_label"):
            invalid.validate()

    def test_atomic_write_validate_and_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = write_trial_atomic(root, metadata(), arrays(), [{"frame_id": 0}])
            loaded = validate_trial_directory(path)
            self.assertEqual(loaded.verified_label, "STROKE")
            with np.load(path / "matrix.npz", allow_pickle=False) as archive:
                self.assertEqual(archive["matrix"].shape, (4, 2, 3))
            summary = summarize_trial(path)
            self.assertEqual(summary["matrix_shape"], [4, 2, 3])
            self.assertEqual(summary["changed_frame_transitions"], 3)
            with self.assertRaises(FileExistsError):
                write_trial_atomic(root, metadata(), arrays(), [])

    def test_manifest_excludes_redo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "raw"
            output = Path(directory) / "gold.csv"
            write_trial_atomic(root, metadata(), arrays(), [])
            redo = metadata("REDO")
            redo = redo.__class__(**{**redo.to_dict(), "trial_id": "trial_000002"})
            write_trial_atomic(root, redo, arrays(), [])
            self.assertEqual(build_gold_manifest(root, output), 1)
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["verified_label"], "STROKE")

    def test_recollection_plan_excludes_old_valid_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "raw"
            output = Path(directory) / "gold.csv"
            plan = Path(directory) / "plan.csv"
            first = metadata()
            first = first.__class__(
                **{**first.to_dict(), "planned_trial_id": "trial_000001", "attempt_no": 1}
            )
            write_trial_atomic(root, first, arrays(), [])
            plan.write_text(
                "operator_id,session_id,planned_trial_id,minimum_attempt_no,reason\n"
                "operator_01,session_01,trial_000001,2,pulse protocol misunderstood\n",
                encoding="utf-8",
            )
            self.assertEqual(build_gold_manifest(root, output, plan), 0)
            second = first.__class__(
                **{**first.to_dict(), "trial_id": "trial_000001_attempt_02", "attempt_no": 2}
            )
            write_trial_atomic(root, second, arrays(), [])
            self.assertEqual(build_gold_manifest(root, output, plan), 1)
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["trial_id"], "trial_000001_attempt_02")

    def test_trial_json_is_plain_and_round_trippable(self):
        payload = metadata().to_dict()
        self.assertEqual(json.loads(json.dumps(payload))["schema_version"], "deepskin-trial-v1")

    def test_observed_sampling_rate_uses_changed_matrices_not_poll_rate(self):
        source = arrays()
        source["matrix"][1] = source["matrix"][0]
        finalized = finalize_metadata(metadata(), source)
        self.assertAlmostEqual(finalized.host_poll_rate_hz, 4 / 0.06)
        self.assertAlmostEqual(finalized.sampling_rate_observed_hz, 3 / 0.06)

    def test_session_order_is_balanced_reproducible_and_non_overwriting(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.csv"
            second = root / "second.csv"
            schedule = REPO_ROOT / "protocol" / "gesture_variation_schedule.csv"
            order_module.write_order("operator_01", "session_01", 20260820, schedule, first)
            order_module.write_order("operator_01", "session_01", 20260820, schedule, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with first.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            labels = [row["instruction_label"] for row in rows]
            self.assertEqual(len(labels), 35)
            self.assertEqual({label: labels.count(label) for label in set(labels)}, {label: 5 for label in order_module.GESTURES})
            self.assertFalse(order_module.has_long_run(labels))
            with self.assertRaises(FileExistsError):
                order_module.write_order("operator_01", "session_01", 20260820, schedule, first)

    def test_session_resume_uses_new_attempt_and_skips_completed_gold(self):
        redo = metadata("REDO")
        redo = redo.__class__(
            **{
                **redo.to_dict(),
                "planned_trial_id": "trial_000001",
                "attempt_no": 1,
            }
        )
        self.assertFalse(session_module.completed_gold([redo]))
        self.assertEqual(
            session_module.next_attempt("trial_000001", [redo]),
            ("trial_000001_attempt_02", 2),
        )
        valid = metadata()
        valid = valid.__class__(
            **{
                **valid.to_dict(),
                "planned_trial_id": "trial_000001",
                "attempt_no": 2,
            }
        )
        self.assertTrue(session_module.completed_gold([redo, valid]))
        self.assertFalse(session_module.completed_gold([redo, valid], minimum_attempt_no=3))


if __name__ == "__main__":
    unittest.main()

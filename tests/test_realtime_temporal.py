import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deepskin_temporal.realtime import (
    RealtimeLabelStabilizer,
    is_sustained_realtime_label,
    summarize_inference_times,
)
from deepskin_temporal.sequence import extract_realtime_window


class RealtimeTemporalTests(unittest.TestCase):
    def test_hybrid_routing_keeps_episode_classes_off_partial_window_output(self):
        for label in ("RUB", "STATIC_TOUCH", "STROKE"):
            self.assertTrue(is_sustained_realtime_label(label), label)
        for label in ("TAP", "POKE", "IMPACT", "PAT"):
            self.assertFalse(is_sustained_realtime_label(label), label)

    def test_window_uses_latest_frames_and_fixed_baseline(self):
        timestamps = np.arange(0.0, 3000.0, 20.0)
        matrix = np.zeros((len(timestamps), 18, 29), dtype=np.float32)
        matrix[timestamps >= 2500.0, 8, 14] = 8.0
        sequence, mask = extract_realtime_window(
            matrix, timestamps, np.zeros((18, 29)), window_ms=1000.0, max_frames=64)
        self.assertEqual(sequence.shape, (64, 21))
        self.assertEqual(mask.sum(), 51)
        self.assertGreater(sequence[:int(mask.sum()), 0].max(), 0.0)

    def test_initial_and_switch_debounce(self):
        gate = RealtimeLabelStabilizer(confidence_threshold=0.5,
                                       initial_confirmations=3, switch_confirmations=2)
        self.assertIsNone(gate.update("RUB", 0.9).current_label)
        self.assertIsNone(gate.update("RUB", 0.9).current_label)
        accepted = gate.update("RUB", 0.9)
        self.assertEqual(accepted.current_label, "RUB")
        self.assertTrue(accepted.changed)
        self.assertEqual(gate.update("PAT", 0.9).current_label, "RUB")
        switched = gate.update("PAT", 0.9)
        self.assertEqual(switched.current_label, "PAT")

    def test_low_confidence_does_not_erase_current_label(self):
        gate = RealtimeLabelStabilizer(initial_confirmations=1)
        gate.update("PAT", 0.9)
        result = gate.update("RUB", 0.2)
        self.assertEqual(result.current_label, "PAT")
        self.assertEqual(result.state, "low_confidence")
        self.assertIsNone(gate.reset().current_label)

    def test_fast_initial_confirmation_only_applies_to_named_label(self):
        gate = RealtimeLabelStabilizer(initial_confirmations=3,
                                       fast_initial_confirmations={"PAT": 2})
        self.assertIsNone(gate.update("PAT", 0.9).current_label)
        self.assertEqual(gate.update("PAT", 0.9).current_label, "PAT")
        gate.reset()
        self.assertIsNone(gate.update("RUB", 0.9).current_label)
        self.assertIsNone(gate.update("RUB", 0.9).current_label)
        self.assertEqual(gate.update("RUB", 0.9).current_label, "RUB")

    def test_inference_summary_reports_budget_overruns(self):
        summary = summarize_inference_times([10.0, 20.0, 120.0], 100.0)
        self.assertEqual(summary["samples"], 3)
        self.assertAlmostEqual(summary["mean_ms"], 50.0)
        self.assertEqual(summary["max_ms"], 120.0)
        self.assertEqual(summary["recent_overruns"], 1)


if __name__ == "__main__":
    unittest.main()

import sys, unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from deepskin_data.training import AUGMENTATIONS, extract_features, segment_touch_event, transform_matrix
from deepskin_data.rejection import apply_positive_gate


class TrainingTests(unittest.TestCase):
    def test_positive_gate_accepts_near_and_rejects_far_features(self):
        gate = {"references": {"TAP": np.array([[0.0, 0.0], [1.0, 1.0]])}, "thresholds": {"TAP": 2.0}}
        self.assertTrue(apply_positive_gate(np.array([0.5, 0.5]), "TAP", gate)["accepted"])
        rejected = apply_positive_gate(np.array([10.0, 10.0]), "TAP", gate)
        self.assertFalse(rejected["accepted"])
        self.assertEqual(rejected["output_label"], "UNKNOWN")
        self.assertEqual(apply_positive_gate(np.zeros(2), "TAP", gate, event_found=False)["reason"], "no_touch_event")

    def test_flip_axes_and_multipliers(self):
        x = np.arange(2 * 3 * 4).reshape(2, 3, 4)
        np.testing.assert_array_equal(transform_matrix(x, "horizontal"), x[:, :, ::-1])
        np.testing.assert_array_equal(transform_matrix(x, "vertical"), x[:, ::-1, :])
        np.testing.assert_array_equal(transform_matrix(x, "both"), x[:, ::-1, ::-1])
        self.assertEqual([len(AUGMENTATIONS[x]) for x in AUGMENTATIONS], [1, 2, 4])

    def test_feature_vector_is_finite_and_fixed(self):
        x = np.zeros((5, 18, 29)); x[:, 4, 6] = np.arange(5)
        a, names = extract_features(x, np.arange(5) * 20.0)
        b, other = extract_features(transform_matrix(x, "horizontal"), np.arange(5) * 20.0)
        self.assertEqual(names, other); self.assertEqual(a.shape, b.shape)
        self.assertTrue(np.isfinite(a).all()); self.assertTrue(np.isfinite(b).all())

    def test_segment_selects_longest_activity_with_padding(self):
        x = np.zeros((100, 18, 29)); t = np.arange(100) * 10.0
        x[30:41, 4, 5] = 8; x[60:63, 4, 5] = 8
        selected, selected_t, info = segment_touch_event(x, t, gap_ms=20, pad_ms=20)
        self.assertTrue(info["found"]); self.assertEqual(info["start_ms"], 300.0)
        self.assertEqual(info["end_ms"], 400.0); self.assertEqual(selected.shape[0], 15)
        self.assertEqual(selected_t[0], 0.0)

if __name__ == "__main__": unittest.main()

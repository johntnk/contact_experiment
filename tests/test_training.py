import sys, unittest
from pathlib import Path
import numpy as np
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from deepskin_data.training import AUGMENTATIONS, domain_class_sample_weights, extract_common_features, extract_features, segment_touch_event, transform_matrix
from deepskin_data.rejection import apply_positive_gate
from deepskin_data.streaming import (ContactEventDetector, apply_episode_label_rule,
                                     count_micro_contacts, episode_gate_reference_label)
from deepskin_data.cost import audit_cost_csv, compatibility_filter_decision, compatibility_metrics


class TrainingTests(unittest.TestCase):
    def test_pat_episode_rule_counts_separated_contacts_and_ignores_short_bounce(self):
        timestamps = np.arange(100, dtype=float) * 10.0
        matrix = np.zeros((100, 3, 4), dtype=float)
        matrix[10:31, 1, 2] = 8.0
        matrix[50:76, 1, 2] = 8.0
        self.assertEqual(count_micro_contacts(matrix, timestamps), 2)
        self.assertEqual(apply_episode_label_rule("IMPACT", 2),
                         ("PAT", "impact_to_pat_repeated_episode"))
        self.assertEqual(apply_episode_label_rule("IMPACT", 1), ("IMPACT", "model"))
        self.assertEqual(apply_episode_label_rule("RUB", 2), ("RUB", "model"))
        self.assertEqual(episode_gate_reference_label("IMPACT", "impact_to_pat_repeated_episode"), "IMPACT")

        bounce = np.zeros_like(matrix)
        bounce[10:31, 1, 2] = 8.0
        bounce[34:36, 1, 2] = 8.0
        self.assertEqual(count_micro_contacts(bounce, timestamps), 1)

    def test_stream_detector_debounces_aggregates_and_completes(self):
        detector = ContactEventDetector(start_debounce_ms=20, end_hold_ms=50, pre_roll_ms=20)
        events, starts = [], 0
        for index in range(30):
            frame = np.zeros((3, 4), dtype=float)
            if 5 <= index <= 9 or 12 <= index <= 16:
                frame[1, 2] = 8
            update = detector.update(frame, index * 10.0)
            starts += int(update.contact_started)
            if update.completed is not None: events.append(update.completed)
        self.assertEqual(starts, 1)
        self.assertEqual(len(events), 1)
        self.assertFalse(events[0].forced_max_duration)
        self.assertGreater(events[0].matrix.shape[0], 12)

    def test_stream_detector_forces_max_duration_and_checks_timestamps(self):
        detector = ContactEventDetector(start_debounce_ms=0, end_hold_ms=50, max_event_ms=30)
        completed = None
        for index in range(5):
            frame = np.full((2, 2), 8.0)
            update = detector.update(frame, index * 10.0)
            completed = update.completed or completed
        self.assertIsNotNone(completed)
        self.assertTrue(completed.forced_max_duration)
        with self.assertRaisesRegex(ValueError, "monotonic"):
            detector.update(np.zeros((2, 2)), 1.0)

    def test_cost_compatibility_filter_applies_frozen_bounds(self):
        config = {"rules": {"tap": {"pulse_count": {"eq": 1}}}}
        self.assertEqual(compatibility_filter_decision("tap", {"pulse_count": 1}, config)[0], "KEPT")
        status, reason = compatibility_filter_decision("tap", {"pulse_count": 2}, config)
        self.assertEqual(status, "FILTERED_AMBIGUOUS")
        self.assertIn("pulse_count_not_eq_1", reason)
        self.assertEqual(compatibility_filter_decision("poke", {}, config)[0], "KEPT")

    def test_cost_compatibility_metrics_count_pulses_and_motion(self):
        matrix = np.zeros((80, 8, 8), dtype=float)
        matrix[10:20, 2, 1:4] = 20
        matrix[35:50, 2, 2:6] = 20
        result = compatibility_metrics(matrix)
        self.assertEqual(result["pulse_count"], 2)
        self.assertEqual(result["complete_release_count"], 1)
        self.assertGreater(result["contact_area_ratio"], 0)
        self.assertTrue(0 <= result["trajectory_straightness"] <= 1)

    def test_domain_class_weights_balance_classes_and_domain_ratio(self):
        labels = np.asarray(["A", "A", "B", "A", "B", "B", "B"])
        domains = np.asarray(["target", "target", "target", "source", "source", "source", "source"])
        weights = domain_class_sample_weights(labels, domains, source_alpha=0.25)
        self.assertAlmostEqual(weights[domains == "target"].sum(), 3.0)
        self.assertAlmostEqual(weights[domains == "source"].sum(), 0.75)
        for domain in ("target", "source"):
            totals = [weights[(domains == domain) & (labels == label)].sum() for label in ("A", "B")]
            self.assertAlmostEqual(totals[0], totals[1])

    def test_common_features_are_finite_and_shape_independent(self):
        t = np.arange(12, dtype=float) * 10.0
        a, names_a = extract_common_features(np.arange(12 * 8 * 8, dtype=float).reshape(12, 8, 8), t)
        b, names_b = extract_common_features(np.arange(12 * 18 * 29, dtype=float).reshape(12, 18, 29), t)
        self.assertEqual(names_a, names_b)
        self.assertEqual(a.shape, b.shape)
        self.assertTrue(np.isfinite(a).all() and np.isfinite(b).all())

    def test_cost_audit_splits_frame_reset_and_maps_only_frozen_labels(self):
        header = ["subject", "variant", "gesture", "frame"] + [f"ch{i}" for i in range(1, 65)]
        rows = [
            [1, 1, 13, 1] + [0] * 64,
            [1, 1, 13, 2] + [1] * 64,
            [1, 1, 13, 1] + [2] * 64,
            [1, 1, 1, 1] + [3] * 64,
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cost.csv"
            path.write_text(", ".join(header) + "\n" + "\n".join(", ".join(map(str, row)) for row in rows), encoding="utf-8")
            report, captures = audit_cost_csv(path)
        self.assertEqual(report["capture_count"], 3)
        self.assertEqual([row["mapped_label"] for row in captures], ["TAP", "TAP", ""])
        self.assertEqual([row["frame_count"] for row in captures], [2, 1, 1])

    def test_positive_gate_accepts_near_and_rejects_far_features(self):
        gate = {"references": {"TAP": np.array([[0.0, 0.0], [1.0, 1.0]])}, "thresholds": {"TAP": 2.0}}
        self.assertTrue(apply_positive_gate(np.array([0.5, 0.5]), "TAP", gate)["accepted"])
        rejected = apply_positive_gate(np.array([10.0, 10.0]), "TAP", gate)
        self.assertFalse(rejected["accepted"])
        self.assertEqual(rejected["output_label"], "UNKNOWN")
        self.assertEqual(apply_positive_gate(np.zeros(2), "TAP", gate, event_found=False)["reason"], "no_touch_event")

    def test_positive_gate_threshold_scale_changes_acceptance(self):
        gate = {"references": {"TAP": np.array([[0.0, 0.0]])}, "thresholds": {"TAP": 2.0}}
        strict = apply_positive_gate(np.array([1.5, 0.0]), "TAP", gate, threshold_scale=0.5)
        relaxed = apply_positive_gate(np.array([1.5, 0.0]), "TAP", gate, threshold_scale=1.25)
        self.assertFalse(strict["accepted"])
        self.assertTrue(relaxed["accepted"])
        self.assertEqual(relaxed["base_threshold"], 2.0)
        self.assertEqual(relaxed["threshold"], 2.5)

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

    def test_stream_baseline_window_does_not_include_long_first_contact(self):
        x = np.zeros((100, 18, 29)); t = np.arange(100) * 10.0
        x[10:51, 4, 5] = 8
        _, _, contaminated = segment_touch_event(x, t)
        _, _, streaming = segment_touch_event(x, t, baseline_window_ms=75.0)
        self.assertFalse(contaminated["found"])
        self.assertTrue(streaming["found"])

if __name__ == "__main__": unittest.main()

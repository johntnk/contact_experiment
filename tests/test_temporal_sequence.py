import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deepskin_temporal.sequence import extract_event_sequence, extract_event_sequence_v2


class TemporalSequenceTests(unittest.TestCase):
    def test_duplicate_timestamps_keep_last_frame(self):
        timestamps = np.array([0.0, 0.0, 20.0, 40.0, 60.0, 80.0, 100.0, 120.0])
        matrix = np.zeros((len(timestamps), 18, 29), dtype=np.float32)
        matrix[0, 3, 4] = 99.0
        matrix[1, 3, 4] = 0.0
        matrix[3:6, 3, 4] = 8.0
        sequence, mask = extract_event_sequence(matrix, timestamps, max_frames=32)
        self.assertEqual(sequence.shape, (32, 21))
        self.assertEqual(mask.shape, (32,))
        self.assertTrue(np.isfinite(sequence).all())
        self.assertGreater(mask.sum(), 1)

    def test_decreasing_timestamps_are_rejected(self):
        matrix = np.zeros((3, 18, 29), dtype=np.float32)
        with self.assertRaisesRegex(ValueError, "non-decreasing"):
            extract_event_sequence(matrix, np.array([0.0, 20.0, 10.0]))

    def test_v2_adds_finite_motion_channels_without_changing_mask(self):
        timestamps = np.arange(0.0, 400.0, 20.0)
        matrix = np.zeros((len(timestamps), 18, 29), dtype=np.float32)
        for index in range(5, 15):
            matrix[index, 8, min(28, index)] = 8.0
        v1, mask1 = extract_event_sequence(matrix, timestamps, max_frames=32)
        v2, mask2 = extract_event_sequence_v2(matrix, timestamps, max_frames=32)
        self.assertEqual(v1.shape, (32, 21))
        self.assertEqual(v2.shape, (32, 27))
        np.testing.assert_array_equal(mask1, mask2)
        self.assertTrue(np.isfinite(v2).all())
        self.assertGreater(v2[:, 26].max(), 0.0)


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from stream_recognize_gui import metric_text


class StreamGuiTests(unittest.TestCase):
    def test_metric_text_handles_missing_gate_value(self):
        self.assertEqual(metric_text(None), "—")
        self.assertEqual(metric_text(3.668354), "3.67")


if __name__ == "__main__":
    unittest.main()

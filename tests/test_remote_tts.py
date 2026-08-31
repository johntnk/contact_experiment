import sys
import unittest
import wave
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from deepskin_tts.remote_api import (
    RemoteSpeechRequest, build_remote_payload, inspect_wav, scale_wav_volume,
)


class RemoteTtsTests(unittest.TestCase):
    def test_payload_contains_required_contract(self):
        payload = build_remote_payload(RemoteSpeechRequest("你好", "excited_high"), "req-1").decode("utf-8")
        self.assertIn('"request_id": "req-1"', payload)
        self.assertIn('"emotion": "excited_high"', payload)
        self.assertIn('"text": "你好"', payload)

    def test_inspects_pcm_wav(self):
        output = BytesIO()
        with wave.open(output, "wb") as stream:
            stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(32000)
            stream.writeframes(b"\0\0" * 32000)
        info = inspect_wav(output.getvalue())
        self.assertEqual(info["sample_rate"], 32000)
        self.assertEqual(info["duration_s"], 1.0)

    def test_scales_pcm_volume_without_changing_format(self):
        output = BytesIO()
        with wave.open(output, "wb") as stream:
            stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(32000)
            stream.writeframes((10000).to_bytes(2, "little", signed=True) * 4)
        scaled = scale_wav_volume(output.getvalue(), 50)
        with wave.open(BytesIO(scaled), "rb") as stream:
            self.assertEqual(stream.getframerate(), 32000)
            sample = int.from_bytes(stream.readframes(1), "little", signed=True)
        self.assertEqual(sample, 5000)

    def test_rejects_invalid_playback_volume(self):
        with self.assertRaises(ValueError):
            RemoteSpeechRequest("text", "excited_high", 101).validate()


if __name__ == "__main__":
    unittest.main()

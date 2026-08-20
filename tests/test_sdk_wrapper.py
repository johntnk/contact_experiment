from __future__ import annotations

import ctypes
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deepskin_runtime.sdk import DeepskinError, DeepskinSDK


class FakeFunction:
    def __init__(self, function):
        self.function = function
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.function(*args)


class FakeDLL:
    def __init__(self, *, init_code: int = 0, enable_code: int = 0) -> None:
        self.calls: list[str] = []
        self.init_code = init_code
        self.enable_code = enable_code
        self.deepskin_init = FakeFunction(self._init)
        self.deepskin_release = FakeFunction(self._release)
        self.deepskin_enable = FakeFunction(self._enable)
        self.deepskin_disable = FakeFunction(self._disable)
        self.deepskin_reset = FakeFunction(self._reset)
        self.deepskin_get_diff_matrix = FakeFunction(self._matrix)
        self.deepskin_get_current_json = FakeFunction(self._json)
        self.deepskin_is_touching = FakeFunction(lambda: 1)
        self.deepskin_get_matrix_size = FakeFunction(self._size)
        self.deepskin_get_last_error = FakeFunction(lambda: b"fake error")

    def _init(self):
        self.calls.append("init")
        return self.init_code

    def _release(self):
        self.calls.append("release")

    def _enable(self):
        self.calls.append("enable")
        return self.enable_code

    def _disable(self):
        self.calls.append("disable")

    def _reset(self):
        self.calls.append("reset")

    @staticmethod
    def _size(tx, rx):
        ctypes.cast(tx, ctypes.POINTER(ctypes.c_int))[0] = 2
        ctypes.cast(rx, ctypes.POINTER(ctypes.c_int))[0] = 3
        return 0

    @staticmethod
    def _matrix(buffer, length):
        for index in range(length):
            buffer[index] = float(index - 1)
        return 0

    @staticmethod
    def _json(buffer, _size):
        payload = b'{"touching":true}'
        ctypes.memmove(buffer, payload + b"\0", len(payload) + 1)
        return 0


class DeepskinSDKTests(unittest.TestCase):
    def make_sdk(self, fake: FakeDLL) -> DeepskinSDK:
        return DeepskinSDK("fake.dll", library=fake)

    def test_lifecycle_and_matrix(self):
        fake = FakeDLL()
        sdk = self.make_sdk(fake)
        sdk.initialize()
        self.assertEqual(sdk.matrix_size(), (2, 3))
        sdk.enable()
        buffer = sdk.allocate_matrix(2, 3)
        sdk.read_matrix(buffer)
        self.assertEqual(list(buffer), [-1.0, 0.0, 1.0, 2.0, 3.0, 4.0])
        self.assertTrue(sdk.is_touching())
        self.assertEqual(sdk.current_json(), '{"touching":true}')
        sdk.close()
        self.assertEqual(fake.calls, ["init", "enable", "disable", "release"])

    def test_context_manager_cleans_up_after_exception(self):
        fake = FakeDLL()
        with self.assertRaisesRegex(RuntimeError, "boom"):
            with self.make_sdk(fake) as sdk:
                sdk.enable()
                raise RuntimeError("boom")
        self.assertEqual(fake.calls, ["init", "enable", "disable", "release"])

    def test_init_failure_copies_error(self):
        fake = FakeDLL(init_code=-1)
        sdk = self.make_sdk(fake)
        with self.assertRaises(DeepskinError) as raised:
            sdk.initialize()
        self.assertEqual(raised.exception.code, -1)
        self.assertEqual(raised.exception.detail, "fake error")
        self.assertFalse(sdk.initialized)

    def test_enable_requires_initialization(self):
        sdk = self.make_sdk(FakeDLL())
        with self.assertRaises(DeepskinError) as raised:
            sdk.enable()
        self.assertEqual(raised.exception.code, -1)


if __name__ == "__main__":
    unittest.main()

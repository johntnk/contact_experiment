"""Small, explicit ctypes wrapper around the public Deepskin x64 SDK."""

from __future__ import annotations

import ctypes
import os
import struct
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any


DEEPSKIN_OK = 0
LOAD_WITH_ALTERED_SEARCH_PATH = 0x00000008
_WORKING_DIRECTORY_LOCK = threading.RLock()


@contextmanager
def _working_directory(path: Path):
    """Temporarily set cwd for the vendor DLL's internal relative LoadLibrary."""
    with _WORKING_DIRECTORY_LOCK:
        previous = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(previous)


class DeepskinError(RuntimeError):
    """Raised when a public SDK call reports an error."""

    def __init__(self, operation: str, code: int, detail: str = "") -> None:
        message = f"{operation} failed with code {code}"
        if detail:
            message += f": {detail}"
        super().__init__(message)
        self.operation = operation
        self.code = code
        self.detail = detail


class DeepskinSDK:
    """Own the SDK lifecycle and copy all DLL-owned strings immediately."""

    def __init__(self, dll_path: str | os.PathLike[str], library: Any | None = None) -> None:
        self.dll_path = Path(dll_path).resolve()
        self._dll = library if library is not None else self._load_library()
        self._initialized = False
        self._enabled = False
        self._configure_signatures()

    def _load_library(self) -> Any:
        if os.name != "nt":
            raise OSError("DeepskinSDK.dll can only be loaded on Windows")
        if struct.calcsize("P") * 8 != 64:
            raise OSError("The stage 1 runtime requires 64-bit Python")
        if not self.dll_path.is_file():
            raise FileNotFoundError(f"SDK DLL not found: {self.dll_path}")
        # The vendor SDK loads HIDdAPI.dll from beside DeepskinSDK.dll during
        # initialization. Make that directory part of dependency resolution
        # even when Python was launched from the repository root.
        return ctypes.WinDLL(
            str(self.dll_path),
            winmode=LOAD_WITH_ALTERED_SEARCH_PATH,
        )

    def _configure_signatures(self) -> None:
        dll = self._dll
        dll.deepskin_init.argtypes = []
        dll.deepskin_init.restype = ctypes.c_int
        dll.deepskin_release.argtypes = []
        dll.deepskin_release.restype = None
        dll.deepskin_enable.argtypes = []
        dll.deepskin_enable.restype = ctypes.c_int
        dll.deepskin_disable.argtypes = []
        dll.deepskin_disable.restype = None
        dll.deepskin_reset.argtypes = []
        dll.deepskin_reset.restype = None
        dll.deepskin_get_diff_matrix.argtypes = [
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_int,
        ]
        dll.deepskin_get_diff_matrix.restype = ctypes.c_int
        dll.deepskin_get_current_json.argtypes = [ctypes.POINTER(ctypes.c_char), ctypes.c_int]
        dll.deepskin_get_current_json.restype = ctypes.c_int
        dll.deepskin_is_touching.argtypes = []
        dll.deepskin_is_touching.restype = ctypes.c_int
        dll.deepskin_get_matrix_size.argtypes = [
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        ]
        dll.deepskin_get_matrix_size.restype = ctypes.c_int
        dll.deepskin_get_last_error.argtypes = []
        dll.deepskin_get_last_error.restype = ctypes.c_char_p

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def enabled(self) -> bool:
        return self._enabled

    def last_error(self) -> str:
        raw = self._dll.deepskin_get_last_error()
        if not raw:
            return ""
        if isinstance(raw, bytes):
            return raw.decode("utf-8", errors="replace")
        return ctypes.cast(raw, ctypes.c_char_p).value.decode("utf-8", errors="replace")

    def _check(self, operation: str, code: int) -> None:
        if code != DEEPSKIN_OK:
            raise DeepskinError(operation, code, self.last_error())

    def initialize(self) -> None:
        if self._initialized:
            return
        # The vendor DLL resolves HIDdAPI.dll relative to the process cwd inside
        # deepskin_init(), rather than relative to DeepskinSDK.dll. Keep this
        # process-global change short, serialized, and exception-safe.
        with _working_directory(self.dll_path.parent):
            code = int(self._dll.deepskin_init())
        self._check("deepskin_init", code)
        self._initialized = True

    def enable(self) -> None:
        if not self._initialized:
            raise DeepskinError("deepskin_enable", -1, "SDK is not initialized")
        if self._enabled:
            return
        code = int(self._dll.deepskin_enable())
        self._check("deepskin_enable", code)
        self._enabled = True

    def matrix_size(self) -> tuple[int, int]:
        if not self._initialized:
            raise DeepskinError("deepskin_get_matrix_size", -1, "SDK is not initialized")
        tx, rx = ctypes.c_int(), ctypes.c_int()
        code = int(self._dll.deepskin_get_matrix_size(ctypes.byref(tx), ctypes.byref(rx)))
        self._check("deepskin_get_matrix_size", code)
        if tx.value <= 0 or rx.value <= 0:
            raise DeepskinError(
                "deepskin_get_matrix_size",
                code,
                f"invalid dimensions {tx.value}x{rx.value}",
            )
        return tx.value, rx.value

    @staticmethod
    def allocate_matrix(tx: int, rx: int) -> Any:
        if tx <= 0 or rx <= 0:
            raise ValueError("matrix dimensions must be positive")
        return (ctypes.c_double * (tx * rx))()

    def read_matrix(self, buffer: Any) -> None:
        if not self._enabled:
            raise DeepskinError("deepskin_get_diff_matrix", -3, "collection is not enabled")
        length = ctypes.sizeof(buffer) // ctypes.sizeof(ctypes.c_double)
        code = int(self._dll.deepskin_get_diff_matrix(buffer, length))
        self._check("deepskin_get_diff_matrix", code)

    def is_touching(self) -> bool:
        if not self._enabled:
            return False
        return bool(self._dll.deepskin_is_touching())

    def current_json(self, buffer_size: int = 4096) -> str:
        if buffer_size <= 1:
            raise ValueError("buffer_size must be greater than 1")
        buffer = ctypes.create_string_buffer(buffer_size)
        code = int(self._dll.deepskin_get_current_json(buffer, buffer_size))
        self._check("deepskin_get_current_json", code)
        return buffer.value.decode("utf-8", errors="replace")

    def reset(self) -> None:
        if not self._initialized:
            raise DeepskinError("deepskin_reset", -1, "SDK is not initialized")
        self._dll.deepskin_reset()

    def close(self) -> None:
        if self._enabled:
            self._dll.deepskin_disable()
            self._enabled = False
        if self._initialized:
            self._dll.deepskin_release()
            self._initialized = False

    def __enter__(self) -> "DeepskinSDK":
        self.initialize()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

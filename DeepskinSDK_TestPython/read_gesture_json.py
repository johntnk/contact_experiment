#!/usr/bin/env python3
"""
电子皮肤 - DeepskinSDK 手势JSON读取示例
输出效果与C++ test_json一致
"""

import ctypes
import time
import sys
import os

# ============================================================
#                   Load DLL
# ============================================================

dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DeepskinSDK.dll")
sdk = ctypes.WinDLL(dll_path)

# API signatures
sdk.deepskin_init.restype = ctypes.c_int
sdk.deepskin_release.restype = None
sdk.deepskin_enable.restype = ctypes.c_int
sdk.deepskin_disable.restype = None
sdk.deepskin_get_matrix_size.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
sdk.deepskin_get_diff_matrix.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
sdk.deepskin_get_diff_matrix.restype = ctypes.c_int
sdk.deepskin_get_gesture.argtypes = [ctypes.c_void_p]
sdk.deepskin_get_gesture.restype = ctypes.c_int
sdk.deepskin_get_recent_gestures_json.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
sdk.deepskin_get_recent_gestures_json.restype = ctypes.c_int
sdk.deepskin_get_last_error.restype = ctypes.c_char_p

# ============================================================
#                   Main
# ============================================================

print("\n=== JSON Output Test ===\n")

if sdk.deepskin_init() != 0:
    print(f"Init failed: {sdk.deepskin_get_last_error()}")
    sys.exit(-1)

tx = ctypes.c_int(0)
rx = ctypes.c_int(0)
sdk.deepskin_get_matrix_size(ctypes.byref(tx), ctypes.byref(rx))

if sdk.deepskin_enable() != 0:
    print("Enable failed")
    sdk.deepskin_release()
    sys.exit(-1)

print("Touch sensor to see JSON...\n")

matrix = (ctypes.c_double * (tx.value * rx.value))()
json_buf = (ctypes.c_char * 32768)()
count = 0

try:
    while True:
        sdk.deepskin_get_diff_matrix(matrix, tx.value * rx.value)

        gesture_buf = (ctypes.c_byte * 1024)()
        if sdk.deepskin_get_gesture(gesture_buf):
            count += 1
            print(f"--- Gesture #{count} ---")

            if sdk.deepskin_get_recent_gestures_json(1, json_buf, 32768) == 0:
                print(json_buf.value.decode("utf-8"))
                print()

        time.sleep(0.05)
except KeyboardInterrupt:
    pass

sdk.deepskin_disable()
sdk.deepskin_release()

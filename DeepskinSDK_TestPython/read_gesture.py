#!/usr/bin/env python3
"""
电子皮肤 - DeepskinSDK 手势检测示例
输出效果与C++ test_gesture一致
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

sdk.deepskin_init.restype = ctypes.c_int
sdk.deepskin_release.restype = None
sdk.deepskin_enable.restype = ctypes.c_int
sdk.deepskin_disable.restype = None
sdk.deepskin_get_diff_matrix.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
sdk.deepskin_get_diff_matrix.restype = ctypes.c_int
sdk.deepskin_get_gesture.argtypes = [ctypes.c_void_p]
sdk.deepskin_get_gesture.restype = ctypes.c_int
sdk.deepskin_get_matrix_size.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
sdk.deepskin_get_last_error.restype = ctypes.c_char_p

# ============================================================
#                   Main
# ============================================================

print("=== Gesture Test ===")
print("1=PalmPress 2=Slap 3=Stroke 4=FistSmash 5=FingerGather 6=SingleTap\n")

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

print("Touch sensor to detect gestures...\n")

matrix = (ctypes.c_double * (tx.value * rx.value))()
count = 0

# Match C++ DeepskinGesture struct layout
GESTURE_NAME_MAP = {
    1: "PalmPress", 2: "Slap", 3: "Stroke",
    4: "FistSmash", 5: "FingerGather", 6: "SingleTap",
}

class DeepskinPeakInfo(ctypes.Structure):
    _fields_ = [("row", ctypes.c_int), ("col", ctypes.c_int), ("value", ctypes.c_int)]

class DeepskinGesture(ctypes.Structure):
    _fields_ = [
        ("gesture_type", ctypes.c_int),
        ("gesture_name", ctypes.c_char_p),
        ("start_frame", ctypes.c_int),
        ("end_frame", ctypes.c_int),
        ("duration_frames", ctypes.c_int),
        ("duration_ms", ctypes.c_double),
        ("force_max", ctypes.c_int),
        ("force_avg", ctypes.c_int),
        ("force_min", ctypes.c_int),
        ("force_peak", ctypes.c_int),
        ("force_std_dev", ctypes.c_double),
        ("force_energy", ctypes.c_double),
        ("area_max", ctypes.c_int),
        ("area_avg", ctypes.c_int),
        ("area_min", ctypes.c_int),
        ("area_std_dev", ctypes.c_double),
        ("contact_ratio", ctypes.c_double),
        ("top_peaks", DeepskinPeakInfo * 5),
        ("top_peaks_count", ctypes.c_int),
        ("total_peak_count", ctypes.c_int),
        ("centroid_start_x", ctypes.c_double),
        ("centroid_start_y", ctypes.c_double),
        ("centroid_end_x", ctypes.c_double),
        ("centroid_end_y", ctypes.c_double),
        ("drift", ctypes.c_double),
        ("drift_x", ctypes.c_double),
        ("drift_y", ctypes.c_double),
        ("total_distance", ctypes.c_double),
        ("velocity_avg", ctypes.c_double),
        ("velocity_max", ctypes.c_double),
        ("acceleration_avg", ctypes.c_double),
        ("shape_width", ctypes.c_int),
        ("shape_height", ctypes.c_int),
        ("shape_aspect_ratio", ctypes.c_double),
        ("shape_perimeter", ctypes.c_double),
        ("shape_convexity", ctypes.c_double),
        ("shape_eccentricity", ctypes.c_double),
        ("shape_fill_ratio", ctypes.c_double),
        ("spread_max", ctypes.c_double),
        ("spread_avg", ctypes.c_double),
        ("spread_min", ctypes.c_double),
        ("spread_std_dev", ctypes.c_double),
        ("centroid_variance_x", ctypes.c_double),
        ("centroid_variance_y", ctypes.c_double),
    ]

try:
    while True:
        sdk.deepskin_get_diff_matrix(matrix, tx.value * rx.value)

        gesture = DeepskinGesture()
        if sdk.deepskin_get_gesture(ctypes.byref(gesture)):
            count += 1
            gname = GESTURE_NAME_MAP.get(gesture.gesture_type, f"Unknown({gesture.gesture_type})")
            print(f"#{count}  type={gesture.gesture_type}  force={gesture.force_max}  area={gesture.area_max}  dur={gesture.duration_ms:.0f}ms")

        time.sleep(0.05)
except KeyboardInterrupt:
    pass

sdk.deepskin_disable()
sdk.deepskin_release()

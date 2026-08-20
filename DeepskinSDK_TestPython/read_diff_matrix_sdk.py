#!/usr/bin/env python3
"""
电子皮肤 - DeepskinSDK Diff Matrix Reader
In-place updating matrix display (same as C++ test_matrix)
"""

import ctypes
import time
import numpy as np
import sys
import os
import msvcrt

# ============================================================
#                   Type Definitions
# ============================================================

class DeepskinPeakInfo(ctypes.Structure):
    _fields_ = [
        ("row", ctypes.c_int),
        ("col", ctypes.c_int),
        ("value", ctypes.c_int),
    ]

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

# ============================================================
#                   Console Helper
# ============================================================

# Windows console handle for cursor movement
kernel32 = ctypes.windll.kernel32

class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

hConsole = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE

def move_cursor(x, y):
    """Move console cursor to position"""
    kernel32.SetConsoleCursorPosition(hConsole, COORD(x, y))

# ============================================================
#                   Main Program
# ============================================================

def main():
    # Set console title
    kernel32.SetConsoleTitleW("DeepskinSDK - Matrix Viewer")

    # 1. Load DeepskinSDK.dll
    dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DeepskinSDK.dll")
    try:
        sdk = ctypes.WinDLL(dll_path)
    except Exception as e:
        print(f"Load DLL failed: {e}")
        return False

    # 2. Configure API
    sdk.deepskin_init.restype = ctypes.c_int
    sdk.deepskin_init.argtypes = []
    sdk.deepskin_release.restype = None
    sdk.deepskin_release.argtypes = []
    sdk.deepskin_enable.restype = ctypes.c_int
    sdk.deepskin_enable.argtypes = []
    sdk.deepskin_disable.restype = None
    sdk.deepskin_disable.argtypes = []
    sdk.deepskin_get_diff_matrix.restype = ctypes.c_int
    sdk.deepskin_get_diff_matrix.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    sdk.deepskin_get_matrix_size.restype = ctypes.c_int
    sdk.deepskin_get_matrix_size.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
    sdk.deepskin_is_touching.restype = ctypes.c_int
    sdk.deepskin_is_touching.argtypes = []
    sdk.deepskin_get_last_error.restype = ctypes.c_char_p
    sdk.deepskin_get_last_error.argtypes = []

    # 3. Init
    print("=== Matrix Test ===\n")
    if sdk.deepskin_init() != 0:
        print(f"Init failed: {sdk.deepskin_get_last_error()}")
        return False

    tx = ctypes.c_int(0)
    rx = ctypes.c_int(0)
    sdk.deepskin_get_matrix_size(ctypes.byref(tx), ctypes.byref(rx))
    print(f"Matrix: {tx.value} x {rx.value}\n")

    # 4. Enable
    if sdk.deepskin_enable() != 0:
        print("Enable failed")
        sdk.deepskin_release()
        return False

    # 5. Main loop - in-place update
    total = tx.value * rx.value
    matrix_buf = (ctypes.c_double * total)()
    frame_count = 0

    # Save cursor position after header
    move_cursor(0, 3)

    try:
        while True:
            sdk.deepskin_get_diff_matrix(matrix_buf, total)
            diff = np.array(matrix_buf, dtype=np.float64)

            # Move cursor back to start of matrix area
            move_cursor(0, 3)

            # Print matrix (tx rows, rx cols) - only positive values shown
            for y in range(tx.value):
                for x in range(rx.value):
                    val = int(diff[y * rx.value + x])
                    if val > 0:
                        sys.stdout.write(f"{val:4d} ")
                    else:
                        sys.stdout.write("     ")
                sys.stdout.write("\n")

            frame_count += 1
            touching = sdk.deepskin_is_touching()
            sys.stdout.write(f"\nFrame: {frame_count}  Touch: {'YES' if touching else 'no'}       \n")
            sys.stdout.write("\nPress Q to quit                    \n")
            sys.stdout.flush()

            # Check Q key
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch in (b'q', b'Q'):
                    break

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    # Cleanup
    move_cursor(0, 3 + rx.value + 3)
    print("\nStopping...")
    sdk.deepskin_disable()
    sdk.deepskin_release()
    print("Done")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Deepskin SDK desktop monitor for Windows."""

from __future__ import annotations

import ctypes
import json
import os
import tkinter as tk
from ctypes import wintypes
from tkinter import messagebox, ttk


DEEPSKIN_OK = 0
GESTURE_NAMES = {
    0: "None",
    1: "PalmPress / 手掌按压",
    2: "Slap / 拍打",
    3: "Stroke / 轻抚",
    4: "FistSmash / 拳头砸击",
    5: "FingerGather / 五指聚拢",
    6: "SingleTap / 单指轻触",
}


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


class DeepskinSDK:
    def __init__(self) -> None:
        dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DeepskinSDK.dll")
        self.dll = ctypes.WinDLL(dll_path)
        self._configure_api()
        self.started = False

    def _configure_api(self) -> None:
        api = self.dll
        api.deepskin_init.argtypes = []
        api.deepskin_init.restype = ctypes.c_int
        api.deepskin_release.argtypes = []
        api.deepskin_release.restype = None
        api.deepskin_enable.argtypes = []
        api.deepskin_enable.restype = ctypes.c_int
        api.deepskin_disable.argtypes = []
        api.deepskin_disable.restype = None
        api.deepskin_reset.argtypes = []
        api.deepskin_reset.restype = None
        api.deepskin_get_matrix_size.argtypes = [
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
        ]
        api.deepskin_get_matrix_size.restype = ctypes.c_int
        api.deepskin_get_diff_matrix.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.c_int
        ]
        api.deepskin_get_diff_matrix.restype = ctypes.c_int
        api.deepskin_get_gesture.argtypes = [ctypes.POINTER(DeepskinGesture)]
        api.deepskin_get_gesture.restype = ctypes.c_int
        api.deepskin_get_recent_gestures_json.argtypes = [
            ctypes.c_int, ctypes.POINTER(ctypes.c_char), ctypes.c_int
        ]
        api.deepskin_get_recent_gestures_json.restype = ctypes.c_int
        api.deepskin_is_touching.argtypes = []
        api.deepskin_is_touching.restype = ctypes.c_int
        api.deepskin_get_last_error.argtypes = []
        api.deepskin_get_last_error.restype = ctypes.c_char_p

    def error(self) -> str:
        raw = self.dll.deepskin_get_last_error()
        return raw.decode("utf-8", errors="replace") if raw else "未知错误"

    def start(self) -> tuple[int, int]:
        result = self.dll.deepskin_init()
        if result != DEEPSKIN_OK:
            raise RuntimeError(self.error())
        tx, rx = ctypes.c_int(), ctypes.c_int()
        result = self.dll.deepskin_get_matrix_size(ctypes.byref(tx), ctypes.byref(rx))
        if result != DEEPSKIN_OK or tx.value <= 0 or rx.value <= 0:
            self.dll.deepskin_release()
            raise RuntimeError(self.error() or "无法读取矩阵尺寸")
        result = self.dll.deepskin_enable()
        if result != DEEPSKIN_OK:
            self.dll.deepskin_release()
            raise RuntimeError(self.error())
        self.started = True
        return tx.value, rx.value

    def stop(self) -> None:
        if self.started:
            self.dll.deepskin_disable()
            self.dll.deepskin_release()
            self.started = False


class DeepskinApp(tk.Tk):
    FRAME_MS = 70

    def __init__(self) -> None:
        super().__init__()
        self.title("Deepskin 实时监控")
        self.geometry("1180x760")
        self.minsize(920, 620)
        self.configure(bg="#0b1220")
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.sdk: DeepskinSDK | None = None
        self.tx = self.rx = 0
        self.matrix = None
        self.cells: list[int] = []
        self.frame_count = 0
        self.gesture_count = 0
        self.paused = False
        self.max_scale = 1200.0

        self.status_text = tk.StringVar(value="正在连接设备…")
        self.touch_text = tk.StringVar(value="未触摸")
        self.frame_text = tk.StringVar(value="帧 0")
        self.peak_text = tk.StringVar(value="峰值 0")
        self._build_ui()
        self.after(100, self.connect)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0b1220")
        style.configure("Card.TFrame", background="#111c2f")
        style.configure("TLabel", background="#0b1220", foreground="#dbeafe")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 18, "bold"))
        style.configure("Muted.TLabel", foreground="#8da2c0")
        style.configure("Card.TLabel", background="#111c2f", foreground="#dbeafe")
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Treeview", background="#101a2b", fieldbackground="#101a2b", foreground="#dbeafe", rowheight=30)
        style.configure("Treeview.Heading", background="#1d2b43", foreground="#e5efff")

        header = ttk.Frame(self, padding=(22, 16))
        header.pack(fill="x")
        ttk.Label(header, text="Deepskin 实时监控", style="Title.TLabel").pack(side="left")
        ttk.Label(header, textvariable=self.status_text, style="Muted.TLabel").pack(side="left", padx=20)
        ttk.Button(header, text="重置基线", command=self.reset, style="Accent.TButton").pack(side="right", padx=(8, 0))
        self.pause_button = ttk.Button(header, text="暂停", command=self.toggle_pause)
        self.pause_button.pack(side="right")

        content = ttk.Panedwindow(self, orient="horizontal")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        left = ttk.Frame(content, style="Card.TFrame", padding=16)
        right = ttk.Frame(content, style="Card.TFrame", padding=16)
        content.add(left, weight=3)
        content.add(right, weight=2)

        meter = ttk.Frame(left, style="Card.TFrame")
        meter.pack(fill="x", pady=(0, 12))
        for textvar in (self.touch_text, self.frame_text, self.peak_text):
            ttk.Label(meter, textvariable=textvar, style="Card.TLabel", font=("Microsoft YaHei UI", 11, "bold")).pack(side="left", padx=(0, 24))

        self.canvas = tk.Canvas(left, bg="#07101e", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._layout_cells())

        ttk.Label(right, text="手势事件", style="Card.TLabel", font=("Microsoft YaHei UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        columns = ("id", "gesture", "force", "area", "duration")
        self.events = ttk.Treeview(right, columns=columns, show="headings", height=9)
        headings = {"id": "#", "gesture": "手势", "force": "力度", "area": "面积", "duration": "时长"}
        widths = {"id": 42, "gesture": 150, "force": 65, "area": 60, "duration": 75}
        for column in columns:
            self.events.heading(column, text=headings[column])
            self.events.column(column, width=widths[column], anchor="center")
        self.events.pack(fill="x")

        ttk.Label(right, text="最近一次手势 JSON", style="Card.TLabel", font=("Microsoft YaHei UI", 12, "bold")).pack(anchor="w", pady=(18, 8))
        self.json_text = tk.Text(
            right, bg="#08111f", fg="#b9d6ff", insertbackground="white",
            relief="flat", font=("Cascadia Mono", 9), padx=10, pady=10, wrap="none"
        )
        self.json_text.pack(fill="both", expand=True)
        self.json_text.insert("1.0", "等待手势事件…")
        self.json_text.configure(state="disabled")

    def connect(self) -> None:
        try:
            self.sdk = DeepskinSDK()
            self.tx, self.rx = self.sdk.start()
            self.matrix = (ctypes.c_double * (self.tx * self.rx))()
            self.status_text.set(f"● 已连接  |  矩阵 {self.tx} × {self.rx}")
            self._create_cells()
            self.after(self.FRAME_MS, self.poll)
        except Exception as exc:
            self.status_text.set("● 连接失败")
            messagebox.showerror("Deepskin 连接失败", f"无法启动传感器：\n\n{exc}\n\n请确认 USB 已连接，且没有其他程序占用设备。")

    def _create_cells(self) -> None:
        self.canvas.delete("all")
        self.cells = [self.canvas.create_rectangle(0, 0, 1, 1, fill="#102038", outline="#172a43") for _ in range(self.tx * self.rx)]
        self._layout_cells()

    def _layout_cells(self) -> None:
        if not self.cells or self.tx <= 0 or self.rx <= 0:
            return
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        gap = 2
        cell_w, cell_h = width / self.rx, height / self.tx
        for row in range(self.tx):
            for col in range(self.rx):
                x0, y0 = col * cell_w + gap, row * cell_h + gap
                x1, y1 = (col + 1) * cell_w, (row + 1) * cell_h
                self.canvas.coords(self.cells[row * self.rx + col], x0, y0, x1, y1)

    @staticmethod
    def _heat_color(value: float, scale: float) -> str:
        level = max(0.0, min(value / max(scale, 1.0), 1.0))
        if level < 0.33:
            t = level / 0.33
            rgb = (8, int(55 + 130 * t), int(110 + 110 * t))
        elif level < 0.66:
            t = (level - 0.33) / 0.33
            rgb = (int(20 + 235 * t), int(185 + 55 * t), int(220 - 170 * t))
        else:
            t = (level - 0.66) / 0.34
            rgb = (255, int(240 - 190 * t), int(50 - 35 * t))
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def poll(self) -> None:
        if not self.sdk or not self.sdk.started:
            return
        try:
            if not self.paused:
                result = self.sdk.dll.deepskin_get_diff_matrix(self.matrix, self.tx * self.rx)
                if result == DEEPSKIN_OK:
                    values = [max(0.0, value) for value in self.matrix]
                    peak = max(values, default=0.0)
                    self.max_scale = max(500.0, self.max_scale * 0.97, peak)
                    for cell, value in zip(self.cells, values):
                        self.canvas.itemconfigure(cell, fill=self._heat_color(value, self.max_scale))
                    self.frame_count += 1
                    self.frame_text.set(f"帧 {self.frame_count}")
                    self.peak_text.set(f"峰值 {peak:.0f}")
                touching = bool(self.sdk.dll.deepskin_is_touching())
                self.touch_text.set("● 正在触摸" if touching else "○ 未触摸")
                gesture = DeepskinGesture()
                if self.sdk.dll.deepskin_get_gesture(ctypes.byref(gesture)):
                    self._add_gesture(gesture)
        except Exception as exc:
            self.status_text.set(f"读取失败：{exc}")
        finally:
            if self.sdk and self.sdk.started:
                self.after(self.FRAME_MS, self.poll)

    def _add_gesture(self, gesture: DeepskinGesture) -> None:
        self.gesture_count += 1
        name = GESTURE_NAMES.get(gesture.gesture_type, f"Unknown ({gesture.gesture_type})")
        self.events.insert("", 0, values=(self.gesture_count, name, gesture.force_max, gesture.area_max, f"{gesture.duration_ms:.0f} ms"))
        children = self.events.get_children()
        if len(children) > 30:
            self.events.delete(*children[30:])

        buffer = ctypes.create_string_buffer(32768)
        result = self.sdk.dll.deepskin_get_recent_gestures_json(1, buffer, len(buffer))
        if result == DEEPSKIN_OK:
            raw = buffer.value.decode("utf-8", errors="replace")
            try:
                raw = json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                pass
            self.json_text.configure(state="normal")
            self.json_text.delete("1.0", "end")
            self.json_text.insert("1.0", raw)
            self.json_text.configure(state="disabled")

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_button.configure(text="继续" if self.paused else "暂停")
        self.status_text.set("● 已暂停" if self.paused else f"● 已连接  |  矩阵 {self.tx} × {self.rx}")

    def reset(self) -> None:
        if self.sdk and self.sdk.started:
            self.sdk.dll.deepskin_reset()
            self.max_scale = 1200.0
            self.status_text.set("● 基线已重置")
            self.after(1200, lambda: self.status_text.set(f"● 已连接  |  矩阵 {self.tx} × {self.rx}"))

    def close(self) -> None:
        if self.sdk:
            self.sdk.stop()
        self.destroy()


def main() -> int:
    app = DeepskinApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

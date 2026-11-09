#!/usr/bin/env python3
"""Controlled desktop UI for the packaged Deepskin social-touch v2 model."""

from __future__ import annotations

import json, sys, threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.recorder import collect_frames
from deepskin_data.rejection import apply_positive_gate
from deepskin_data.training import extract_features, segment_touch_event, transform_matrix
from deepskin_runtime import DeepskinSDK

DLL = ROOT / "DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll"
MODEL_DIR = ROOT / "models/deepskin_social_touch_v2"
LABELS = ["不指定", "STATIC_TOUCH", "STROKE", "RUB", "TAP", "POKE", "PAT", "IMPACT"]
ORIENTATIONS = {"正常方向 (0°)": "original", "旋转 180°": "both"}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Deepskin 社会触摸识别 v2")
        self.geometry("760x520"); self.minsize(700, 480)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.model = joblib.load(MODEL_DIR / "model.joblib")
        self.gate = joblib.load(MODEL_DIR / "positive_gate.joblib")
        self.schema = json.loads((MODEL_DIR / "feature_schema.json").read_text(encoding="utf-8"))
        self.sdk = None; self.busy = False
        self.status = tk.StringVar(value="正在连接 Deepskin…")
        self.expected = tk.StringVar(value="不指定")
        self.orientation = tk.StringVar(value="正常方向 (0°)")
        self.result = tk.StringVar(value="尚未识别")
        self.detail = tk.StringVar(value="选择动作后点击开始，或选择“不指定”进行自由识别。")
        self._build(); threading.Thread(target=self._connect, daemon=True).start()

    def _build(self):
        style = ttk.Style(self); style.configure("Title.TLabel", font=("Microsoft YaHei UI", 20, "bold")); style.configure("Result.TLabel", font=("Microsoft YaHei UI", 32, "bold")); style.configure("Big.TButton", font=("Microsoft YaHei UI", 14), padding=12)
        root = ttk.Frame(self, padding=24); root.pack(fill="both", expand=True)
        ttk.Label(root, text="Deepskin 社会触摸识别", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, textvariable=self.status, foreground="#2867b2").pack(anchor="w", pady=(4, 20))
        controls = ttk.Frame(root); controls.pack(fill="x")
        ttk.Label(controls, text="期望动作：").pack(side="left")
        self.combo = ttk.Combobox(controls, textvariable=self.expected, values=LABELS, state="readonly", width=20); self.combo.pack(side="left", padx=8)
        ttk.Label(controls, text="传感器方向：").pack(side="left", padx=(12, 0))
        self.orientation_combo = ttk.Combobox(controls, textvariable=self.orientation, values=list(ORIENTATIONS), state="readonly", width=16); self.orientation_combo.pack(side="left", padx=8)
        self.button = ttk.Button(controls, text="开始识别", style="Big.TButton", command=self.start, state="disabled"); self.button.pack(side="right")
        card = ttk.LabelFrame(root, text="识别结果", padding=22); card.pack(fill="both", expand=True, pady=24)
        ttk.Label(card, textvariable=self.result, style="Result.TLabel").pack(pady=(25, 18))
        ttk.Label(card, textvariable=self.detail, justify="center", wraplength=620).pack()
        ttk.Label(root, text="模型 v2 · 事件分段 · 7 类 · 每次采集 4 秒", foreground="#666").pack(anchor="center")

    def _connect(self):
        try:
            sdk = DeepskinSDK(DLL); sdk.initialize(); sdk.enable()
            if sdk.matrix_size() != (18, 29): raise ValueError("设备矩阵尺寸不是 18×29")
            self.sdk = sdk; self.after(0, lambda: (self.status.set("● 已连接 · 矩阵 18×29"), self.button.configure(state="normal")))
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("连接失败", str(exc)))
            self.after(0, lambda: self.status.set("连接失败，请检查 USB 和设备占用"))

    def start(self):
        if self.busy or self.sdk is None: return
        self.busy = True; self.button.configure(state="disabled"); self.combo.configure(state="disabled"); self.orientation_combo.configure(state="disabled")
        self._countdown(3)

    def _countdown(self, remaining):
        if remaining:
            self.result.set(str(remaining)); self.detail.set("保持传感器空闲，倒计时结束后执行动作")
            self.after(1000, lambda: self._countdown(remaining - 1))
        else:
            self.result.set("采集中…"); self.detail.set("现在执行动作；完成后完全抬手")
            threading.Thread(target=self._capture, daemon=True).start()

    def _capture(self):
        try:
            arrays, _ = collect_frames(self.sdk, 4.0, 5.0)
            orientation_label = self.orientation.get()
            orientation_transform = ORIENTATIONS[orientation_label]
            canonical_matrix = transform_matrix(arrays["matrix"], orientation_transform)
            matrix, timestamps, segment = segment_touch_event(canonical_matrix, arrays["timestamps_ms"])
            feature, names = extract_features(matrix, timestamps)
            if names != self.schema: raise ValueError("特征定义与模型不一致")
            prediction = str(self.model.predict(feature.reshape(1, -1))[0]); scores = self.model.decision_function(feature.reshape(1, -1))[0]
            scaled_feature = self.model.named_steps["standardscaler"].transform(feature.reshape(1, -1))[0]
            gate_result = apply_positive_gate(scaled_feature, prediction, self.gate, bool(segment.get("found")))
            output_label = gate_result["output_label"]
            ranked = sorted(zip(self.model.classes_, scores), key=lambda x: x[1], reverse=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f"); out = ROOT / "artifacts/live_validation/gui_runs"; out.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(out / f"{stamp}.npz", **arrays)
            payload = {"predicted_label": prediction, "output_label": output_label, "positive_gate": gate_result, "expected_label": None if self.expected.get()=="不指定" else self.expected.get(), "sensor_orientation": orientation_label, "orientation_transform": orientation_transform, "raw_matrix_orientation": "device_native", "ranked_scores": [{"label":str(k),"score":float(v)} for k,v in ranked], "segment_info":segment, "raw_file":f"{stamp}.npz"}
            (out / f"{stamp}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            duration = segment.get("end_ms", 0) - segment.get("start_ms", 0) if segment.get("found") else 0
            gate_text = f"可信距离 {gate_result['distance']:.2f} / 阈值 {gate_result['threshold']:.2f}" if gate_result["distance"] is not None else "未检测到有效触摸事件"
            detail = ("Top-3：" + "  ·  ".join(f"{k} {v:.2f}" for k,v in ranked[:3]) + f"\n{gate_text} · 事件持续约 {duration:.0f} ms · 已保存 {stamp}")
            shown_label = output_label if gate_result["accepted"] else "未识别（已忽略）"
            self.after(0, lambda: self._finish(shown_label, detail))
        except Exception as exc:
            self.after(0, lambda: self._finish("识别失败", str(exc)))

    def _finish(self, prediction, detail):
        self.result.set(prediction); self.detail.set(detail); self.busy=False; self.button.configure(state="normal"); self.combo.configure(state="readonly"); self.orientation_combo.configure(state="readonly")

    def close_app(self):
        if self.busy and not messagebox.askyesno("正在采集", "采集尚未结束，仍要关闭吗？"): return
        if self.sdk is not None:
            try: self.sdk.close()
            except Exception: pass
        self.destroy()


if __name__ == "__main__": App().mainloop()

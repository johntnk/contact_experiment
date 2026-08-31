#!/usr/bin/env python3
"""Experimental continuous GUI for the V2 temporal TCN."""

from __future__ import annotations

import argparse
import json
import queue
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from deepskin_data.streaming import ContactEventDetector, count_micro_contacts
from deepskin_data.training import transform_matrix
from deepskin_runtime import DeepskinSDK
from deepskin_temporal.model import SmallTCN
from deepskin_temporal.sequence import extract_event_sequence, extract_event_sequence_v2

DLL = ROOT / "DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll"
MODEL_DIR = ROOT / "models/deepskin_temporal_tcn_adapted_v1"
ORIENTATIONS = {"正常方向（0°）": "original", "旋转 180°": "both"}


class TemporalApp(tk.Tk):
    def __init__(self, model_dir: Path = MODEL_DIR) -> None:
        super().__init__()
        self.title("Deepskin TCN 连续识别（实验版）")
        self.geometry("900x650"); self.minsize(820, 590)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = torch.load(model_dir / "model.pt", map_location=self.device, weights_only=False)
        self.feature_version = str(checkpoint.get("feature_version", "v1"))
        self.sequence_extractor = extract_event_sequence_v2 if self.feature_version == "v2" else extract_event_sequence
        input_channels = int(checkpoint.get("input_channels", 21))
        self.model = SmallTCN(input_channels=input_channels).to(self.device)
        self.model.load_state_dict(checkpoint["model_state"]); self.model.eval()
        self.mean = np.asarray(checkpoint["channel_mean"], dtype=np.float32)
        self.std = np.asarray(checkpoint["channel_std"], dtype=np.float32)
        self.labels = list(checkpoint["labels"])
        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop_event = threading.Event(); self.worker: threading.Thread | None = None; self.running = False
        self.status = tk.StringVar(value="设备未启动")
        self.result = tk.StringVar(value="等待启动")
        self.detail = tk.StringVar(value="TCN 实验模型不会覆盖 V1；启动后完成动作并完全抬手。")
        self.probability = tk.StringVar(value="Top-3：—")
        self.orientation = tk.StringVar(value="正常方向（0°）")
        self.threshold = tk.DoubleVar(value=0.50); self.current_threshold = 0.50
        self.threshold.trace_add("write", self._update_threshold)
        self._build(); self.after(50, self._drain)

    def _build(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 20, "bold"))
        style.configure("Result.TLabel", font=("Microsoft YaHei UI", 34, "bold"))
        style.configure("Big.TButton", font=("Microsoft YaHei UI", 12, "bold"), padding=10)
        root = ttk.Frame(self, padding=20); root.pack(fill="both", expand=True)
        ttk.Label(root, text="Deepskin TCN 连续识别", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="实验版 · 完整时序模型 · 不替换 V1", foreground="#b45f06").pack(anchor="w", pady=(2, 4))
        ttk.Label(root, textvariable=self.status, foreground="#2867b2").pack(anchor="w", pady=(0, 14))

        controls = ttk.LabelFrame(root, text="运行参数", padding=12); controls.pack(fill="x")
        ttk.Label(controls, text="传感器方向").grid(row=0, column=0, sticky="w")
        self.orientation_box = ttk.Combobox(controls, textvariable=self.orientation, values=list(ORIENTATIONS),
                                            state="readonly", width=18)
        self.orientation_box.grid(row=1, column=0, padx=(0, 18), sticky="w")
        ttk.Label(controls, text="输出置信度阈值").grid(row=0, column=1, sticky="w")
        ttk.Spinbox(controls, from_=0.0, to=1.0, increment=0.05, textvariable=self.threshold,
                    width=9).grid(row=1, column=1, sticky="w")
        ttk.Label(controls, text="低于阈值显示“已忽略”；此阈值尚未完成开放集校准。",
                  foreground="#666").grid(row=1, column=2, padx=15, sticky="w")

        params = ttk.LabelFrame(root, text="固定事件参数", padding=10); params.pack(fill="x", pady=(10, 0))
        ttk.Label(params, text="起始阈值 3.0　基线余量 2.0　开始防抖 40 ms　结束保持 550 ms　预滚动 150 ms",
                  foreground="#555").pack(anchor="w")
        ttk.Label(params, text="结果在最后一次抬手约 0.6 秒后出现；PAT 请在同一区域轻拍 2～4 次。",
                  foreground="#555").pack(anchor="w", pady=(3, 0))

        actions = ttk.Frame(root); actions.pack(fill="x", pady=12)
        self.start_button = ttk.Button(actions, text="启动 TCN 连续识别", style="Big.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="停止", style="Big.TButton", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        ttk.Label(actions, text=f"推理设备：{self.device}", foreground="#666").pack(side="left", padx=10)

        card = ttk.LabelFrame(root, text="识别结果", padding=18); card.pack(fill="both", expand=True)
        ttk.Label(card, textvariable=self.result, style="Result.TLabel").pack(pady=(16, 10))
        ttk.Label(card, textvariable=self.probability, font=("Microsoft YaHei UI", 12)).pack(pady=5)
        ttk.Label(card, textvariable=self.detail, justify="center", wraplength=760).pack(pady=6)
        ttk.Label(card, text="三折 OOF Macro F1 0.8623；该实验模型未通过正式 V1 替换门槛。",
                  foreground="#777").pack(side="bottom")

    def _update_threshold(self, *_args) -> None:
        try:
            value = float(self.threshold.get())
            if 0 <= value <= 1: self.current_threshold = value
        except (ValueError, tk.TclError): pass

    def start(self) -> None:
        if self.running: return
        self.running = True; self.stop_event.clear(); self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal"); self.orientation_box.configure(state="disabled")
        self.status.set("正在连接设备…"); self.result.set("等待触摸")
        orientation = ORIENTATIONS[self.orientation.get()]
        self.worker = threading.Thread(target=self._run, args=(orientation,), daemon=True); self.worker.start()

    def stop(self) -> None:
        if self.running: self.status.set("正在停止…"); self.stop_event.set()

    def _classify(self, matrix, timestamps, orientation):
        canonical = transform_matrix(matrix, orientation)
        sequence, mask = self.sequence_extractor(canonical, timestamps, baseline_window_ms=75.0)
        scaled = (((sequence - self.mean) / self.std) * mask[..., None]).astype(np.float32)
        with torch.inference_mode():
            logits = self.model(torch.from_numpy(scaled[None]).to(self.device),
                                torch.from_numpy(mask[None]).to(self.device))
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()
        order = np.argsort(probabilities)[::-1]
        ranked = [(self.labels[index], float(probabilities[index])) for index in order]
        pulses = count_micro_contacts(canonical, timestamps)
        return ranked, pulses

    def _run(self, orientation: str) -> None:
        detector = ContactEventDetector(start_threshold=3.0, baseline_margin=2.0,
                                        start_debounce_ms=40.0, end_hold_ms=550.0,
                                        pre_roll_ms=150.0, max_event_ms=8000.0)
        started = time.monotonic()
        try:
            with DeepskinSDK(DLL) as sdk:
                sdk.enable(); rows, cols = sdk.matrix_size()
                if (rows, cols) != (18, 29): raise ValueError(f"模型要求 18×29，设备返回 {rows}×{cols}")
                buffer = sdk.allocate_matrix(rows, cols); self.messages.put(("status", "● 设备已连接并持续采样"))
                while not self.stop_event.is_set():
                    sdk.read_matrix(buffer); timestamp = (time.monotonic() - started) * 1000.0
                    update = detector.update(np.asarray(buffer, dtype=float).reshape(rows, cols), timestamp)
                    if update.contact_started: self.messages.put(("contact", None))
                    if update.completed is not None:
                        ranked, pulses = self._classify(update.completed.matrix, update.completed.timestamps_ms, orientation)
                        self.messages.put(("result", {"ranked": ranked, "pulses": pulses,
                                                       "threshold": self.current_threshold}))
                    time.sleep(0.005)
        except Exception as exc: self.messages.put(("error", str(exc)))
        finally: self.messages.put(("stopped", None))

    def _drain(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "status": self.status.set(str(payload))
                elif kind == "contact": self.result.set("检测中…"); self.detail.set("完全抬手后输出最终时序结果。")
                elif kind == "result": self._show(payload)  # type: ignore[arg-type]
                elif kind == "error": messagebox.showerror("TCN 连续识别失败", str(payload))
                elif kind == "stopped":
                    self.running = False; self.status.set("设备已停止")
                    self.start_button.configure(state="normal"); self.stop_button.configure(state="disabled")
                    self.orientation_box.configure(state="readonly")
        except queue.Empty: pass
        self.after(50, self._drain)

    def _show(self, payload: dict) -> None:
        ranked = payload["ranked"]; label, confidence = ranked[0]; threshold = payload["threshold"]
        accepted = confidence >= threshold
        self.result.set(label if accepted else "已忽略")
        self.probability.set("Top-3：" + "　".join(f"{name} {probability:.1%}" for name, probability in ranked[:3]))
        self.detail.set(f"候选：{label}　置信度：{confidence:.3f}　阈值：{threshold:.2f}　"
                        f"有效脉冲：{payload['pulses']}　结果：{'接受' if accepted else '抑制'}")

    def close_app(self) -> None:
        self.stop_event.set(); self.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    arguments = parser.parse_args()
    TemporalApp(arguments.model_dir).mainloop()

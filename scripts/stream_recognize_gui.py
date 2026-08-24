#!/usr/bin/env python3
"""Continuous Deepskin recognition GUI with an adjustable positive gate."""

from __future__ import annotations

import json
import queue
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from deepskin_data.streaming import ContactEventDetector
from deepskin_runtime import DeepskinSDK
from stream_recognize import classify_event

DLL = ROOT / "DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll"
MODEL_DIR = ROOT / "models/deepskin_social_touch_v2"
ORIENTATIONS = {"正常方向（0°）": "original", "旋转 180°": "both"}


def metric_text(value: object) -> str:
    """Format an optional gate metric without crashing the Tk callback."""
    if value is None:
        return "—"
    return f"{float(value):.2f}"


class StreamApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Deepskin 连续手势识别")
        self.geometry("940x780")
        self.minsize(860, 700)
        self.protocol("WM_DELETE_WINDOW", self.close_app)

        self.model = joblib.load(MODEL_DIR / "model.joblib")
        self.gate = joblib.load(MODEL_DIR / "positive_gate.joblib")
        self.schema = json.loads((MODEL_DIR / "feature_schema.json").read_text(encoding="utf-8"))
        self.config = json.loads((MODEL_DIR / "training_config.json").read_text(encoding="utf-8"))

        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.running = False

        self.status = tk.StringVar(value="设备未启动")
        self.result = tk.StringVar(value="等待启动")
        self.candidate = tk.StringVar(value="候选类别：—")
        self.gate_detail = tk.StringVar(value="门控距离：—　有效阈值：—　结果：—")
        self.event_detail = tk.StringVar(value="检测到完整触摸事件后，只显示通过门控的目标动作。")
        self.orientation = tk.StringVar(value="正常方向（0°）")
        self.gate_scale = tk.DoubleVar(value=1.2)
        self.current_gate_scale = 1.2
        self.gate_scale.trace_add("write", self._update_gate_scale)
        self.start_threshold = tk.DoubleVar(value=3.0)
        self.baseline_margin = tk.DoubleVar(value=2.0)
        self.start_debounce = tk.DoubleVar(value=40.0)
        self.end_hold = tk.DoubleVar(value=550.0)

        self._build()
        self.after(50, self._drain_messages)

    def _build(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 20, "bold"))
        style.configure("Result.TLabel", font=("Microsoft YaHei UI", 34, "bold"))
        style.configure("Big.TButton", font=("Microsoft YaHei UI", 12, "bold"), padding=10)

        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Deepskin 连续手势识别", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, textvariable=self.status, foreground="#2867b2").pack(anchor="w", pady=(3, 14))

        controls = ttk.LabelFrame(root, text="运行与事件检测参数", padding=12)
        controls.pack(fill="x")
        self._field(controls, "传感器方向", ttk.Combobox(
            controls, textvariable=self.orientation, values=list(ORIENTATIONS), state="readonly", width=17), 0)
        self._field(controls, "起始阈值", ttk.Spinbox(
            controls, from_=0.1, to=100, increment=0.5, textvariable=self.start_threshold, width=9), 1)
        self._field(controls, "基线余量", ttk.Spinbox(
            controls, from_=0, to=100, increment=0.5, textvariable=self.baseline_margin, width=9), 2)
        self._field(controls, "开始防抖 ms", ttk.Spinbox(
            controls, from_=0, to=1000, increment=10, textvariable=self.start_debounce, width=9), 3)
        self._field(controls, "结束保持 ms", ttk.Spinbox(
            controls, from_=10, to=3000, increment=50, textvariable=self.end_hold, width=9), 4)

        detector_help = ttk.LabelFrame(root, text="事件检测参数说明", padding=10)
        detector_help.pack(fill="x", pady=(10, 0))
        explanations = (
            ("起始阈值", "信号至少达到该值才可能开始触摸。调低更灵敏但更容易受噪声影响；调高可抗噪但可能漏掉轻触。"),
            ("基线余量", "实际阈值 = max(起始阈值, 空闲噪声中位数 + 基线余量)。调高可抵抗基线漂移，但会降低轻触灵敏度。"),
            ("开始防抖", "信号必须连续超过阈值这么久，才确认事件开始。用于过滤瞬时尖峰；过长可能漏掉很短的 TAP 或 IMPACT。"),
            ("结束保持", "信号回落后持续这么久才确认事件结束。默认 550 ms，用于聚合 PAT 的 2～4 次轻拍；两次轻拍间隔应小于约 0.5 秒。"),
        )
        for row, (name, description) in enumerate(explanations):
            ttk.Label(detector_help, text=f"{name}：", font=("Microsoft YaHei UI", 9, "bold"),
                      width=11, anchor="e").grid(row=row, column=0, sticky="ne", padx=(0, 5), pady=2)
            ttk.Label(detector_help, text=description, wraplength=760, justify="left",
                      foreground="#555").grid(row=row, column=1, sticky="w", pady=2)
        detector_help.columnconfigure(1, weight=1)

        gate_box = ttk.LabelFrame(root, text="正类门控（调试）", padding=12)
        gate_box.pack(fill="x", pady=(12, 0))
        ttk.Label(gate_box, text="阈值倍率").grid(row=0, column=0, sticky="w")
        self.scale_spin = ttk.Spinbox(gate_box, from_=0.1, to=3.0, increment=0.05,
                                      textvariable=self.gate_scale, width=9)
        self.scale_spin.grid(row=1, column=0, sticky="w", padx=(0, 18))
        ttk.Label(gate_box, text="< 1 更严格；> 1 更宽松。修改后对下一个完整事件生效。",
                  foreground="#666").grid(row=1, column=1, sticky="w")

        columns = tuple(sorted(self.gate["thresholds"]))
        table = ttk.Treeview(gate_box, columns=columns, show="headings", height=1)
        for label in columns:
            table.heading(label, text=label)
            table.column(label, width=90, anchor="center")
        table.insert("", "end", values=[f"{float(self.gate['thresholds'][x]):.2f}" for x in columns])
        table.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        gate_box.columnconfigure(1, weight=1)

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=12)
        self.start_button = ttk.Button(actions, text="启动连续识别", style="Big.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="停止", style="Big.TButton", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        ttk.Label(actions, text="设备在启动到停止期间始终保持开启；不会自动保存原始数据。",
                  foreground="#666").pack(side="left", padx=8)

        card = ttk.LabelFrame(root, text="实时识别结果", padding=18)
        card.pack(fill="both", expand=True)
        ttk.Label(card, textvariable=self.result, style="Result.TLabel").pack(pady=(15, 12))
        ttk.Label(card, textvariable=self.candidate, font=("Microsoft YaHei UI", 12)).pack()
        ttk.Label(card, textvariable=self.gate_detail, font=("Consolas", 11)).pack(pady=8)
        ttk.Label(card, textvariable=self.event_detail, justify="center", wraplength=760).pack()

    @staticmethod
    def _field(parent, label: str, widget: ttk.Widget, column: int) -> None:
        ttk.Label(parent, text=label).grid(row=0, column=column, sticky="w", padx=(0, 12))
        widget.grid(row=1, column=column, sticky="w", padx=(0, 12))

    def _parameters(self) -> dict[str, float | str]:
        values = {
            "orientation": ORIENTATIONS[self.orientation.get()],
            "start_threshold": float(self.start_threshold.get()),
            "baseline_margin": float(self.baseline_margin.get()),
            "start_debounce_ms": float(self.start_debounce.get()),
            "end_hold_ms": float(self.end_hold.get()),
        }
        if values["start_threshold"] <= 0 or values["baseline_margin"] < 0:
            raise ValueError("起始阈值必须大于 0，基线余量不能为负数")
        if values["start_debounce_ms"] < 0 or values["end_hold_ms"] <= 0:
            raise ValueError("防抖时间不能为负数，结束保持时间必须大于 0")
        if float(self.gate_scale.get()) <= 0:
            raise ValueError("门控阈值倍率必须大于 0")
        return values

    def _update_gate_scale(self, *_args) -> None:
        try:
            value = float(self.gate_scale.get())
            if np.isfinite(value) and value > 0:
                self.current_gate_scale = value
        except (ValueError, tk.TclError):
            pass

    def start(self) -> None:
        if self.running:
            return
        try:
            parameters = self._parameters()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("参数无效", str(exc))
            return
        self.running = True
        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status.set("正在连接设备…")
        self.result.set("等待触摸")
        self.worker = threading.Thread(target=self._run, args=(parameters,), daemon=True)
        self.worker.start()

    def stop(self) -> None:
        if self.running:
            self.status.set("正在停止…")
            self.stop_event.set()

    def _run(self, parameters: dict[str, float | str]) -> None:
        detector = ContactEventDetector(
            start_threshold=float(parameters["start_threshold"]),
            baseline_margin=float(parameters["baseline_margin"]),
            start_debounce_ms=float(parameters["start_debounce_ms"]),
            end_hold_ms=float(parameters["end_hold_ms"]),
            max_event_ms=8000.0,
        )
        started = time.monotonic()
        try:
            with DeepskinSDK(DLL) as sdk:
                sdk.enable()
                rows, cols = sdk.matrix_size()
                if (rows, cols) != (18, 29):
                    raise ValueError(f"模型要求 18×29，设备返回 {rows}×{cols}")
                buffer = sdk.allocate_matrix(rows, cols)
                self.messages.put(("status", "● 设备已连接并持续采样"))
                while not self.stop_event.is_set():
                    sdk.read_matrix(buffer)
                    now_ms = (time.monotonic() - started) * 1000.0
                    update = detector.update(np.asarray(buffer, dtype=float).reshape(rows, cols), now_ms)
                    if update.contact_started:
                        self.messages.put(("contact", None))
                    if update.completed is not None:
                        scale = self.current_gate_scale
                        prediction, ranked, gate_result, segment = classify_event(
                            update.completed, self.model, self.gate, self.schema, self.config,
                            str(parameters["orientation"]), scale)
                        self.messages.put(("result", {
                            "prediction": prediction,
                            "ranked": ranked,
                            "gate": gate_result,
                            "segment": segment,
                            "scale": scale,
                        }))
                    time.sleep(0.005)
        except Exception as exc:
            self.messages.put(("error", str(exc)))
        finally:
            self.messages.put(("stopped", None))

    def _drain_messages(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "status":
                    self.status.set(str(payload))
                elif kind == "contact":
                    self.result.set("检测中…")
                    self.event_detail.set("触摸事件尚未结束；完全抬手后给出最终结果。")
                elif kind == "result":
                    self._show_result(payload)  # type: ignore[arg-type]
                elif kind == "error":
                    messagebox.showerror("连续识别失败", str(payload))
                elif kind == "stopped":
                    self.running = False
                    self.status.set("设备已停止")
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(50, self._drain_messages)

    def _show_result(self, payload: dict) -> None:
        gate = payload["gate"]
        prediction = payload["prediction"]
        accepted = bool(gate["accepted"])
        self.result.set(prediction if accepted else "已忽略")
        segment = payload.get("segment", {})
        model_prediction = segment.get("model_prediction", prediction)
        pulse_count = segment.get("micro_contact_count", "—")
        if segment.get("classification_rule") == "impact_to_pat_repeated_episode":
            candidate_text = f"模型候选：{model_prediction}　Episode 修正：PAT　有效脉冲：{pulse_count}"
        else:
            candidate_text = f"候选类别：{prediction}　有效脉冲：{pulse_count}"
        self.candidate.set(candidate_text)
        self.gate_detail.set(
            f"门控距离：{metric_text(gate.get('distance'))}　"
            f"原始阈值：{metric_text(gate.get('base_threshold'))}　"
            f"倍率：{metric_text(gate.get('threshold_scale', payload['scale']))}　"
            f"有效阈值：{metric_text(gate.get('threshold'))}　"
            f"结果：{'接受' if accepted else '抑制'}")
        top3 = "　".join(f"{label} {score:.2f}" for label, score in payload["ranked"][:3])
        if gate.get("reason") == "no_touch_event":
            self.event_detail.set("事件分段未找到有效触摸；本次事件已忽略，请稍加力度或检查事件检测参数。")
        else:
            self.event_detail.set(f"Top-3：{top3}\n非目标或低置信度事件不会作为手势输出。")

    def close_app(self) -> None:
        self.stop_event.set()
        self.destroy()


if __name__ == "__main__":
    StreamApp().mainloop()

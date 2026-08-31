#!/usr/bin/env python3
"""Causal sliding-window GUI for continuous Deepskin action output."""

from __future__ import annotations

import argparse
from collections import deque
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
from deepskin_data.streaming import ContactEventDetector
from deepskin_runtime import DeepskinSDK
from deepskin_temporal.model import SmallTCN
from deepskin_temporal.realtime import (
    RealtimeLabelStabilizer,
    is_sustained_realtime_label,
    summarize_inference_times,
)
from deepskin_temporal.sequence import extract_event_sequence, extract_realtime_window


DLL = ROOT / "DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll"
MODEL_DIR = ROOT / "models/deepskin_temporal_tcn_adapted_v1"
ORIENTATIONS = {"正常方向（0°）": "original", "旋转 180°": "both"}


def orient_frame(frame: np.ndarray, orientation: str) -> np.ndarray:
    return frame if orientation == "original" else frame[::-1, ::-1]


class RealtimeApp(tk.Tk):
    def __init__(self, model_dir: Path = MODEL_DIR) -> None:
        super().__init__()
        self.title("Deepskin 实时流式动作识别")
        self.geometry("1120x700")
        self.minsize(1000, 640)
        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        checkpoint = torch.load(model_dir / "model.pt", map_location=self.device, weights_only=False)
        if str(checkpoint.get("feature_version", "v1")) != "v1":
            raise ValueError("实时流式版当前要求 21 通道 v1 特征模型")
        input_channels = int(checkpoint.get("input_channels", 21))
        if input_channels != 21:
            raise ValueError(f"实时流式版要求 21 个输入通道，模型为 {input_channels}")
        self.model = SmallTCN(input_channels=input_channels).to(self.device)
        self.model.load_state_dict(checkpoint["model_state"])
        self.model.eval()
        self.mean = np.asarray(checkpoint["channel_mean"], dtype=np.float32)
        self.std = np.asarray(checkpoint["channel_std"], dtype=np.float32)
        self.labels = list(checkpoint["labels"])

        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.running = False
        self.display_generation = 0
        self.status = tk.StringVar(value="设备未启动")
        self.current = tk.StringVar(value="等待启动")
        self.top3 = tk.StringVar(value="Top-3：—")
        self.detail = tk.StringVar(value="持续接触时每隔一段时间更新当前动作；完全抬手后清空状态。")
        self.performance = tk.StringVar(value="推理监控：尚无样本")
        self.orientation = tk.StringVar(value="正常方向（0°）")
        self.threshold = tk.DoubleVar(value=0.50)
        self.window_ms = tk.IntVar(value=1500)
        self.interval_ms = tk.IntVar(value=100)
        self.initial_confirmations = tk.IntVar(value=3)
        self.pat_initial_confirmations = tk.IntVar(value=2)
        self.impact_initial_confirmations = tk.IntVar(value=2)
        self.switch_confirmations = tk.IntVar(value=2)
        self.release_hold_ms = tk.IntVar(value=300)
        self._build()
        self.after(50, self._drain)

    def _build(self) -> None:
        style = ttk.Style(self)
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 20, "bold"))
        style.configure("Result.TLabel", font=("Microsoft YaHei UI", 36, "bold"))
        style.configure("Big.TButton", font=("Microsoft YaHei UI", 12, "bold"), padding=10)
        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Deepskin 实时流式动作识别", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="滑动窗口 · 持续输出 · 动作切换防抖", foreground="#2867b2").pack(anchor="w")
        ttk.Label(root, textvariable=self.status, foreground="#2867b2").pack(anchor="w", pady=(4, 12))

        controls = ttk.LabelFrame(root, text="实时参数（启动后锁定）", padding=12)
        controls.pack(fill="x")
        fields = [
            ("传感器方向", self.orientation, None),
            ("置信度阈值", self.threshold, (0.0, 1.0, 0.05)),
            ("窗口长度 ms", self.window_ms, (500, 3000, 100)),
            ("更新间隔 ms", self.interval_ms, (50, 500, 50)),
            ("首次确认次数", self.initial_confirmations, (1, 10, 1)),
            ("PAT 首次确认", self.pat_initial_confirmations, (1, 10, 1)),
            ("IMPACT 首次确认", self.impact_initial_confirmations, (1, 10, 1)),
            ("切换确认次数", self.switch_confirmations, (1, 10, 1)),
            ("抬手清空 ms", self.release_hold_ms, (200, 800, 50)),
        ]
        self.parameter_widgets = []
        for column, (label, variable, bounds) in enumerate(fields):
            ttk.Label(controls, text=label).grid(row=0, column=column, padx=5, sticky="w")
            if bounds is None:
                widget = ttk.Combobox(controls, textvariable=variable, values=list(ORIENTATIONS),
                                      state="readonly", width=15)
            else:
                widget = ttk.Spinbox(controls, from_=bounds[0], to=bounds[1], increment=bounds[2],
                                     textvariable=variable, width=11)
            widget.grid(row=1, column=column, padx=5, sticky="w")
            self.parameter_widgets.append(widget)
        ttk.Label(
            controls,
            text="默认：最近 1.5 秒、每 100 ms 推理；普通类别确认 3 次、PAT/IMPACT 确认 2 次；抬手 300 ms 清空。",
            foreground="#666",
        ).grid(row=2, column=0, columnspan=9, padx=5, pady=(8, 0), sticky="w")

        actions = ttk.Frame(root)
        actions.pack(fill="x", pady=12)
        self.start_button = ttk.Button(actions, text="启动实时识别", style="Big.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="停止", style="Big.TButton", command=self.stop,
                                      state="disabled")
        self.stop_button.pack(side="left", padx=10)
        ttk.Label(actions, text=f"推理设备：{self.device}", foreground="#666").pack(side="left", padx=10)

        card = ttk.LabelFrame(root, text="当前动作", padding=18)
        card.pack(fill="both", expand=True)
        ttk.Label(card, textvariable=self.current, style="Result.TLabel").pack(pady=(25, 10))
        ttk.Label(card, textvariable=self.top3, font=("Microsoft YaHei UI", 12)).pack(pady=6)
        ttk.Label(card, textvariable=self.detail, justify="center", wraplength=820).pack(pady=8)
        ttk.Label(card, textvariable=self.performance, foreground="#555").pack(pady=5)
        ttk.Label(
            card,
            text="提示：PAT 需要形成节奏、RUB/STROKE 需要形成轨迹，因此动作开始后仍需短暂积累证据。",
            foreground="#777",
        ).pack(side="bottom")

    def _config(self) -> dict:
        config = {
            "threshold": float(self.threshold.get()),
            "window_ms": int(self.window_ms.get()),
            "interval_ms": int(self.interval_ms.get()),
            "initial": int(self.initial_confirmations.get()),
            "pat_initial": int(self.pat_initial_confirmations.get()),
            "impact_initial": int(self.impact_initial_confirmations.get()),
            "switch": int(self.switch_confirmations.get()),
            "release_hold_ms": int(self.release_hold_ms.get()),
            "orientation": ORIENTATIONS[self.orientation.get()],
        }
        if not 0 <= config["threshold"] <= 1:
            raise ValueError("置信度阈值必须在 0 到 1 之间")
        if not 500 <= config["window_ms"] <= 3000 or not 50 <= config["interval_ms"] <= 500:
            raise ValueError("窗口或更新间隔超出允许范围")
        if config["initial"] < 1 or config["switch"] < 1 or not 200 <= config["release_hold_ms"] <= 800:
            raise ValueError("确认次数必须大于零")
        if not 1 <= config["pat_initial"] <= config["initial"]:
            raise ValueError("PAT 首次确认必须在 1 和普通首次确认次数之间")
        if not 1 <= config["impact_initial"] <= config["initial"]:
            raise ValueError("IMPACT 首次确认必须在 1 和普通首次确认次数之间")
        return config

    def start(self) -> None:
        if self.running:
            return
        try:
            config = self._config()
        except (ValueError, tk.TclError) as exc:
            messagebox.showerror("参数错误", str(exc))
            return
        self.running = True
        self.stop_event.clear()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        for widget in self.parameter_widgets:
            widget.configure(state="disabled")
        self.status.set("正在连接设备…")
        self.current.set("等待接触")
        self.worker = threading.Thread(target=self._run, args=(config,), daemon=True)
        self.worker.start()

    def stop(self) -> None:
        if self.running:
            self.status.set("正在停止…")
            self.stop_event.set()

    def _classify(self, matrix: np.ndarray, timestamps: np.ndarray, baseline: np.ndarray,
                  window_ms: int):
        started = time.perf_counter()
        sequence, mask = extract_realtime_window(
            matrix, timestamps, baseline, window_ms=float(window_ms))
        scaled = (((sequence - self.mean) / self.std) * mask[..., None]).astype(np.float32)
        with torch.inference_mode():
            logits = self.model(
                torch.from_numpy(scaled[None]).to(self.device),
                torch.from_numpy(mask[None]).to(self.device),
            )
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        order = np.argsort(probabilities)[::-1]
        ranked = [(self.labels[index], float(probabilities[index])) for index in order]
        return ranked, elapsed_ms

    def _classify_completed_event(self, matrix: np.ndarray, timestamps: np.ndarray,
                                  orientation: str):
        started = time.perf_counter()
        canonical = matrix if orientation == "original" else matrix[:, ::-1, ::-1]
        sequence, mask = extract_event_sequence(canonical, timestamps, baseline_window_ms=75.0)
        scaled = (((sequence - self.mean) / self.std) * mask[..., None]).astype(np.float32)
        with torch.inference_mode():
            logits = self.model(
                torch.from_numpy(scaled[None]).to(self.device),
                torch.from_numpy(mask[None]).to(self.device),
            )
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        order = np.argsort(probabilities)[::-1]
        return [(self.labels[index], float(probabilities[index])) for index in order], elapsed_ms

    def _run(self, config: dict) -> None:
        detector = ContactEventDetector(
            start_threshold=3.0, baseline_margin=2.0, start_debounce_ms=40.0,
            end_hold_ms=float(config["release_hold_ms"]), pre_roll_ms=150.0,
            max_event_ms=3_600_000.0)
        stabilizer = RealtimeLabelStabilizer(
            confidence_threshold=config["threshold"],
            initial_confirmations=config["initial"],
            switch_confirmations=config["switch"],
            fast_initial_confirmations={"PAT": config["pat_initial"],
                                        "IMPACT": config["impact_initial"]},
        )
        recent: deque[tuple[float, np.ndarray]] = deque()
        baseline = None
        contact_start = None
        last_inference = float("-inf")
        inference_times: deque[float] = deque(maxlen=100)
        total_overruns = 0
        transient_candidate = None
        transient_count = 0
        started = time.monotonic()
        try:
            with DeepskinSDK(DLL) as sdk:
                sdk.enable()
                rows, cols = sdk.matrix_size()
                if (rows, cols) != (18, 29):
                    raise ValueError(f"模型要求 18×29，设备返回 {rows}×{cols}")
                buffer = sdk.allocate_matrix(rows, cols)
                self.messages.put(("status", "● 设备已连接，正在持续采样"))
                while not self.stop_event.is_set():
                    sdk.read_matrix(buffer)
                    timestamp = (time.monotonic() - started) * 1000.0
                    native = np.asarray(buffer, dtype=float).reshape(rows, cols).copy()
                    canonical = orient_frame(native, config["orientation"])
                    recent.append((timestamp, canonical))
                    while recent and timestamp - recent[0][0] > config["window_ms"] + 1000.0:
                        recent.popleft()
                    threshold = detector.threshold
                    active_now = float(np.maximum(native, 0.0).max()) >= threshold
                    update = detector.update(native, timestamp)
                    if update.contact_started:
                        idle = [frame for time_ms, frame in recent if time_ms <= timestamp - 60.0]
                        baseline = np.median(np.stack(idle[-60:] if idle else [recent[0][1]]), axis=0)
                        contact_start = timestamp
                        last_inference = float("-inf")
                        stabilizer.reset()
                        transient_candidate = None
                        transient_count = 0
                        self.messages.put(("contact", None))
                    if detector.active and active_now and baseline is not None and contact_start is not None:
                        enough_evidence = timestamp - contact_start >= 200.0
                        due = timestamp - last_inference >= config["interval_ms"]
                        if enough_evidence and due:
                            selected = [(time_ms, frame) for time_ms, frame in recent
                                        if time_ms >= timestamp - config["window_ms"]]
                            times = np.asarray([item[0] for item in selected], dtype=np.float64)
                            matrices = np.stack([item[1] for item in selected])
                            ranked, inference_ms = self._classify(
                                matrices, times, baseline, config["window_ms"])
                            inference_times.append(inference_ms)
                            if inference_ms > config["interval_ms"]:
                                total_overruns += 1
                            timing = summarize_inference_times(inference_times, config["interval_ms"])
                            top_label, top_confidence = ranked[0]
                            transient_pending = False
                            if is_sustained_realtime_label(top_label):
                                transient_candidate = None
                                transient_count = 0
                                stabilized = stabilizer.update(top_label, top_confidence)
                            else:
                                if top_label == transient_candidate and top_confidence >= config["threshold"]:
                                    transient_count += 1
                                elif top_confidence >= config["threshold"]:
                                    transient_candidate = top_label
                                    transient_count = 1
                                else:
                                    transient_candidate = None
                                    transient_count = 0
                                transient_pending = transient_count >= 2
                                stabilized = stabilizer.reset() if transient_pending else stabilizer.update(top_label, 0.0)
                            self.messages.put(("prediction", {
                                "ranked": ranked,
                                "stabilized": stabilized,
                                "elapsed_ms": timestamp - contact_start,
                                "timing": timing,
                                "total_overruns": total_overruns,
                                "budget_ms": config["interval_ms"],
                                "transient_pending": transient_pending,
                                "transient_candidate": transient_candidate,
                            }))
                            last_inference = timestamp
                    if update.completed is not None:
                        ranked, inference_ms = self._classify_completed_event(
                            update.completed.matrix, update.completed.timestamps_ms,
                            config["orientation"])
                        inference_times.append(inference_ms)
                        if inference_ms > config["interval_ms"]:
                            total_overruns += 1
                        timing = summarize_inference_times(inference_times, config["interval_ms"])
                        self.messages.put(("event_result", {
                            "ranked": ranked,
                            "threshold": config["threshold"],
                            "timing": timing,
                            "total_overruns": total_overruns,
                            "budget_ms": config["interval_ms"],
                        }))
                        stabilizer.reset()
                        baseline = None
                        contact_start = None
                        transient_candidate = None
                        transient_count = 0
                    time.sleep(0.005)
        except Exception as exc:
            self.messages.put(("error", str(exc)))
        finally:
            self.messages.put(("stopped", None))

    def _drain(self) -> None:
        try:
            while True:
                kind, payload = self.messages.get_nowait()
                if kind == "status":
                    self.status.set(str(payload))
                elif kind == "contact":
                    self.display_generation += 1
                    self.current.set("积累证据…")
                    self.detail.set("已检测到接触，正在等待稳定的时序证据。")
                elif kind == "prediction":
                    self._show_prediction(payload)  # type: ignore[arg-type]
                elif kind == "event_result":
                    self._show_event_result(payload)  # type: ignore[arg-type]
                elif kind == "released":
                    self.current.set("等待接触")
                    self.top3.set("Top-3：—")
                    self.detail.set("已完全抬手，实时状态已清空。")
                elif kind == "error":
                    messagebox.showerror("实时识别失败", str(payload))
                elif kind == "stopped":
                    self.running = False
                    self.status.set("设备已停止")
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    for index, widget in enumerate(self.parameter_widgets):
                        widget.configure(state="readonly" if index == 0 else "normal")
        except queue.Empty:
            pass
        self.after(50, self._drain)

    def _show_prediction(self, payload: dict) -> None:
        ranked = payload["ranked"]
        stabilized = payload["stabilized"]
        self.top3.set("Top-3：" + "　".join(f"{label} {probability:.1%}"
                                             for label, probability in ranked[:3]))
        if payload.get("transient_pending"):
            self.current.set("检测短时动作…")
        elif stabilized.current_label is not None:
            self.current.set(stabilized.current_label)
        elif stabilized.state == "low_confidence":
            self.current.set("未知 / 证据不足")
        else:
            self.current.set("积累证据…")
        candidate = stabilized.candidate_label or "—"
        state_text = {
            "confirming": "正在确认",
            "stable": "稳定输出",
            "switched": "已切换",
            "low_confidence": "低置信度，保持上一结果",
        }.get(stabilized.state, stabilized.state)
        self.detail.set(
            f"状态：{state_text}　候选：{candidate}　候选连续次数：{stabilized.candidate_count}　"
            f"接触持续：{payload['elapsed_ms'] / 1000.0:.1f} 秒"
        )
        timing = payload["timing"]
        health = "正常" if timing["recent_overruns"] == 0 else "存在超时"
        self.performance.set(
            f"推理监控：平均 {timing['mean_ms']:.1f} ms　P95 {timing['p95_ms']:.1f} ms　"
            f"最大 {timing['max_ms']:.1f} ms　预算 {payload['budget_ms']} ms　"
            f"最近超时 {timing['recent_overruns']}/{timing['samples']}　"
            f"累计超时 {payload['total_overruns']}　状态：{health}"
        )

    def _show_event_result(self, payload: dict) -> None:
        self.display_generation += 1
        generation = self.display_generation
        ranked = payload["ranked"]
        label, confidence = ranked[0]
        accepted = confidence >= payload["threshold"]
        self.current.set(label if accepted else "未知 / 证据不足")
        self.top3.set("Top-3：" + "　".join(f"{name} {probability:.1%}"
                                             for name, probability in ranked[:3]))
        self.detail.set(
            f"完整事件结果：{label}　置信度：{confidence:.3f}　"
            f"状态：{'已输出' if accepted else '低置信度抑制'}"
        )
        timing = payload["timing"]
        health = "正常" if timing["recent_overruns"] == 0 else "存在超时"
        self.performance.set(
            f"推理监控：平均 {timing['mean_ms']:.1f} ms　P95 {timing['p95_ms']:.1f} ms　"
            f"最大 {timing['max_ms']:.1f} ms　预算 {payload['budget_ms']} ms　"
            f"最近超时 {timing['recent_overruns']}/{timing['samples']}　"
            f"累计超时 {payload['total_overruns']}　状态：{health}"
        )
        self.after(600, lambda: self._clear_completed_result(generation))

    def _clear_completed_result(self, generation: int) -> None:
        if self.running and generation == self.display_generation:
            self.current.set("等待接触")
            self.top3.set("Top-3：—")
            self.detail.set("已完全抬手，实时状态已清空。")

    def close_app(self) -> None:
        self.stop_event.set()
        self.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    args = parser.parse_args()
    RealtimeApp(args.model_dir).mainloop()

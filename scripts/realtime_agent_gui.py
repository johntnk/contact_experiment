#!/usr/bin/env python3
"""Formal Deepskin runtime with a throttled IM Agent SSE bridge."""

from __future__ import annotations

import argparse
import queue
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from deepskin_agent import AgentDispatcher, AgentResult, im_frontend_url
from deepskin_temporal.realtime import is_sustained_realtime_label
from realtime_stream_gui import MODEL_DIR, RealtimeApp


DEFAULT_API_URL = "http://192.168.100.110:5175/api/agent/im/generate"
DEFAULT_USER_ID = "test-user-1"
DEFAULT_SESSION_ID = "web-2026-08-24-5pj76na4"
DEFAULT_FRONTEND_URL = "http://192.168.100.110:5175/"


class RealtimeAgentApp(RealtimeApp):
    def __init__(self, *, model_dir: Path, api_url: str, user_id: str,
                 session_id: str, frontend_url: str, send_interval_s: float) -> None:
        self.agent_messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.agent_api_url = api_url
        self.agent_user_id = user_id
        self.agent_session_id = session_id
        self.frontend_url = frontend_url
        self.send_interval_s = send_interval_s
        self.agent_dispatcher: AgentDispatcher | None = None
        super().__init__(model_dir)
        self.title("Deepskin 实时识别 · Agent 接入")
        self.agent_state = tk.StringVar(value="Agent：等待触摸动作")
        self.agent_response = tk.StringVar(value="最近回复：—")
        self._build_agent_panel()
        self.agent_dispatcher = AgentDispatcher(
            url=api_url,
            user_id=user_id,
            session_id=session_id,
            min_interval_s=send_interval_s,
            timeout_s=20.0,
            on_update=lambda kind, payload: self.agent_messages.put((kind, payload)),
        )
        self.agent_dispatcher.start()

    def _build_agent_panel(self) -> None:
        panel = tk.Toplevel(self)
        panel.title("Agent 接入状态")
        panel.geometry("760x260")
        panel.resizable(True, False)
        panel.protocol("WM_DELETE_WINDOW", panel.withdraw)
        frame = ttk.Frame(panel, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Agent SSE 接入", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(frame, text=f"API：{self.agent_api_url}", wraplength=720).pack(anchor="w", pady=(10, 0))
        ttk.Label(frame, text=f"用户：{self.agent_user_id}    会话：{self.agent_session_id}").pack(anchor="w")
        ttk.Label(frame, text=f"限流：每 {self.send_interval_s:g} 秒最多启动一个请求；积压时只保留最新动作",
                  foreground="#2867b2").pack(anchor="w", pady=(4, 10))
        ttk.Label(frame, textvariable=self.agent_state, font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w")
        ttk.Label(frame, textvariable=self.agent_response, wraplength=720).pack(anchor="w", pady=(5, 10))
        buttons = ttk.Frame(frame)
        buttons.pack(anchor="w")
        ttk.Button(buttons, text="打开用户指定页面",
                   command=lambda: webbrowser.open(self.frontend_url)).pack(side="left")
        im_url = im_frontend_url(self.frontend_url, self.agent_session_id)
        ttk.Button(buttons, text="打开 IM 结果页面",
                   command=lambda: webbrowser.open(im_url)).pack(side="left", padx=8)
        self.agent_panel = panel

    def _submit_agent_label(self, label: str) -> None:
        if self.agent_dispatcher is not None:
            self.agent_dispatcher.submit(label)

    def _show_prediction(self, payload: dict) -> None:
        super()._show_prediction(payload)
        stabilized = payload["stabilized"]
        if stabilized.current_label is not None:
            self._submit_agent_label(stabilized.current_label)

    def _show_event_result(self, payload: dict) -> None:
        super()._show_event_result(payload)
        label, confidence = payload["ranked"][0]
        if confidence >= payload["threshold"] and not is_sustained_realtime_label(label):
            self._submit_agent_label(label)

    def _drain(self) -> None:
        super()._drain()
        try:
            while True:
                kind, payload = self.agent_messages.get_nowait()
                if kind == "sending":
                    self.agent_state.set(f"Agent：正在发送 {payload}")
                elif kind == "done":
                    result = payload
                    if isinstance(result, AgentResult):
                        self.agent_state.set(f"Agent：{result.label} 已完成")
                        self.agent_response.set(f"最近回复：{result.text or '（SSE done 未提供 text）'}")
                        self._on_agent_done(result)
                elif kind == "error":
                    self.agent_state.set("Agent：请求失败；Deepskin 识别仍在运行")
                    self.agent_response.set(f"错误：{payload}")
        except queue.Empty:
            pass

    def _on_agent_done(self, _result: AgentResult) -> None:
        """Extension hook used by the isolated TTS runtime."""

    def close_app(self) -> None:
        if self.agent_dispatcher is not None:
            self.agent_dispatcher.close()
        super().close_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--user-id", default=DEFAULT_USER_ID)
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID)
    parser.add_argument("--frontend-url", default=DEFAULT_FRONTEND_URL)
    parser.add_argument("--send-interval-s", type=float, default=3.0)
    args = parser.parse_args()
    RealtimeAgentApp(
        model_dir=args.model_dir,
        api_url=args.api_url,
        user_id=args.user_id,
        session_id=args.session_id,
        frontend_url=args.frontend_url,
        send_interval_s=args.send_interval_s,
    ).mainloop()

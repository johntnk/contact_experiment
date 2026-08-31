#!/usr/bin/env python3
"""Complete Deepskin -> IM Agent -> remote TTS runtime."""

from __future__ import annotations

import argparse
import queue
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from deepskin_agent import AgentResult
from deepskin_tts import RemoteSpeechRequest, RemoteTtsWorker
from realtime_agent_gui import (
    DEFAULT_API_URL, DEFAULT_FRONTEND_URL, DEFAULT_SESSION_ID, DEFAULT_USER_ID,
    MODEL_DIR, RealtimeAgentApp,
)

DEFAULT_TTS_URL = "http://192.168.102.106:8021/v1/tts"


class RealtimeAgentRemoteTtsApp(RealtimeAgentApp):
    def __init__(self, *, tts_url: str, tts_emotion: str, **kwargs) -> None:
        self.remote_tts_messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.remote_tts_worker: RemoteTtsWorker | None = None
        super().__init__(**kwargs)
        self.title("Deepskin · Agent · 远程 TTS")
        self.tts_enabled = tk.BooleanVar(value=True)
        self.tts_emotion = tk.StringVar(value=tts_emotion)
        self.tts_volume = tk.IntVar(value=100)
        self.tts_state = tk.StringVar(value="远程 TTS：等待 Agent 回复")
        self._build_remote_tts_panel(tts_url)
        self.remote_tts_worker = RemoteTtsWorker(
            url=tts_url, timeout_s=20.0,
            on_update=lambda kind, payload: self.remote_tts_messages.put((kind, payload)),
        )
        self.remote_tts_worker.start()

    def _build_remote_tts_panel(self, tts_url: str) -> None:
        panel = tk.Toplevel(self)
        panel.title("远程 TTS 设置")
        panel.geometry("760x220")
        panel.protocol("WM_DELETE_WINDOW", panel.withdraw)
        frame = ttk.Frame(panel, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="远程情绪 TTS", font=("Microsoft YaHei UI", 16, "bold")).pack(anchor="w")
        ttk.Label(frame, text=f"API：{tts_url}").pack(anchor="w", pady=(8, 3))
        row = ttk.Frame(frame)
        row.pack(fill="x", pady=5)
        ttk.Checkbutton(row, text="启用语音", variable=self.tts_enabled).pack(side="left")
        ttk.Label(row, text="情绪：").pack(side="left", padx=(20, 3))
        ttk.Entry(row, textvariable=self.tts_emotion, width=24).pack(side="left")
        ttk.Label(row, text="音量：").pack(side="left", padx=(20, 3))
        ttk.Spinbox(row, from_=0, to=100, increment=5, textvariable=self.tts_volume,
                    width=7).pack(side="left")
        ttk.Button(row, text="试听", command=self._test_speech).pack(side="left", padx=10)
        ttk.Label(frame, textvariable=self.tts_state, foreground="#2867b2", wraplength=720).pack(anchor="w", pady=8)
        ttk.Label(frame, text="新回复会中断旧语音；临时 WAV 播放后自动删除。", foreground="#666").pack(anchor="w")
        self.remote_tts_panel = panel

    def _speak(self, text: str) -> None:
        if not self.tts_enabled.get() or self.remote_tts_worker is None or not text.strip():
            return
        try:
            self.remote_tts_worker.submit(RemoteSpeechRequest(
                text, self.tts_emotion.get(), int(self.tts_volume.get())))
        except (ValueError, tk.TclError) as exc:
            self.tts_state.set(f"远程 TTS 参数错误：{exc}")

    def _test_speech(self) -> None:
        self._speak("你好，Deepskin 远程语音服务已经连接成功。")

    def _on_agent_done(self, result: AgentResult) -> None:
        self._speak(result.text)

    def _drain(self) -> None:
        super()._drain()
        try:
            while True:
                kind, payload = self.remote_tts_messages.get_nowait()
                if kind == "synthesizing":
                    self.tts_state.set("远程 TTS：正在合成")
                elif kind == "speaking":
                    info = payload["info"]
                    self.tts_state.set(f"远程 TTS：正在播放（{info['duration_s']:.2f} 秒）")
                elif kind == "done":
                    self.tts_state.set("远程 TTS：播放完成")
                elif kind == "error":
                    self.tts_state.set(f"远程 TTS 错误：{payload}")
        except queue.Empty:
            pass

    def close_app(self) -> None:
        if self.remote_tts_worker is not None:
            self.remote_tts_worker.close()
        super().close_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--user-id", default=DEFAULT_USER_ID)
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID)
    parser.add_argument("--frontend-url", default=DEFAULT_FRONTEND_URL)
    parser.add_argument("--send-interval-s", type=float, default=3.0)
    parser.add_argument("--tts-url", default=DEFAULT_TTS_URL)
    parser.add_argument("--tts-emotion", default="excited_high")
    args = parser.parse_args()
    RealtimeAgentRemoteTtsApp(
        model_dir=args.model_dir, api_url=args.api_url, user_id=args.user_id,
        session_id=args.session_id, frontend_url=args.frontend_url,
        send_interval_s=args.send_interval_s, tts_url=args.tts_url,
        tts_emotion=args.tts_emotion,
    ).mainloop()

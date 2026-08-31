# Deepskin Agent + 远程 TTS v1

运行入口：

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\realtime_agent_remote_tts_gui.py
```

默认链路：

- Agent：`http://192.168.100.110:5175/api/agent/im/generate`
- 远程 TTS：`http://192.168.102.106:8021/v1/tts`
- 情绪：`excited_high`
- 播放音量：GUI 可调 0–100，默认 100；仅缩放该次 WAV，不修改系统全局音量
- Agent 请求启动间隔：至少 3 秒

链路为“Deepskin → TCN → IM Agent SSE → 回复文本 → 远程 TTS → 本机播放”。Agent 和 TTS 都使用单槽最新值邮箱，不建立无界队列；新语音到达时中断旧语音。远程 WAV 写入系统临时目录，播放结束或中断后自动删除。

Windows SAPI 本地 TTS 版本已于 2026-08-25 按项目负责人要求永久删除，后续不再使用。

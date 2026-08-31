# Deepskin → IM Agent 接入 v1

## 运行

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\realtime_agent_gui.py
```

默认配置：

- API：`http://192.168.100.110:5175/api/agent/im/generate`
- 前端：`http://192.168.100.110:5175/`
- 用户：`test-user-1`
- 会话：`web-2026-08-24-5pj76na4`
- 发送间隔：3 秒
- 请求超时：20 秒

所有值都可通过 `--api-url`、`--user-id`、`--session-id`、`--frontend-url` 和 `--send-interval-s` 覆盖。

## 背压策略

Agent 网络请求在独立线程执行，不阻塞 Deepskin SDK 采样和 TCN 推理。任何时刻最多有一个请求在途，且相邻请求启动时间至少间隔 3 秒。请求期间出现多个动作时只保留最新动作，不积累无界队列。持续动作每 3 秒最多发送一次；TAP、POKE、IMPACT、PAT 只在完整事件确认后发送。

`done.data.value` 中的 Mood、Favor、Egy 和 Stress 会成为下一次请求的状态。网络错误或 20 秒超时只显示在 Agent 状态窗口，不停止触摸识别。

## 前端限制

用户指定的 `/s/{sessionId}` 是 generic Agent 面板，而本接入调用 IM Agent。IM 结果对应页面为 `/im/{sessionId}`。前端当前没有针对外部写入的自动轮询；若页面已经打开，可能需要刷新才能显示新消息。浏览器当前用户必须与请求的 `x-user-id` 一致（默认 `test-user-1`）。这两项属于远端前端行为，无法仅在 Deepskin 项目中修复。

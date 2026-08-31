# Deepskin 实时混合识别

运行：

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\realtime_stream_gui.py
```

该入口继续使用正式个性化 TCN 模型，不重新训练模型。为了匹配模型的训练输入，运行时按动作性质分成两条路径：

- `RUB`、`STATIC_TOUCH`、`STROKE`：使用最近 1.5 秒的因果滑动窗口，每 100 ms 更新，可在不抬手时连续显示和切换。
- `TAP`、`POKE`、`IMPACT`、`PAT`：接触期间仅显示“检测短时动作…”，抬手并满足 300 ms 结束保持后，用完整事件分类并输出结果。

短时类别采用完整事件路径，是因为当前 TCN 用完整动作训练。把尚未结束的片段直接缩放成完整序列会产生输入分布偏移，表现为 IMPACT/TAP/POKE 下降，以及 PAT 被提前判为 STROKE。代价是四个短时类别必须在动作结束后才能给出最终语义。

默认参数为置信度阈值 0.50、窗口 1500 ms、更新间隔 100 ms、普通首次确认 3 次、动作切换确认 2 次、结束保持 300 ms。GUI 保留最近 100 次推理的平均、P95、最大耗时和超时计数。原始纯滑动窗口版本保存在 `scripts/realtime_stream_gui_v1.py`，正式事件版 `scripts/temporal_stream_gui.py` 也未被覆盖。

开发数据完整事件回放仅作为管线验证：自然 PAT/RUB 数据中 28 个被事件检测器完整截取的样本均分类正确，另有 2 个因录制尾部不足而无法形成完成事件。该数据参与过个性化开发，不能作为独立准确率声明；IMPACT、TAP、POKE 仍需现场验收。

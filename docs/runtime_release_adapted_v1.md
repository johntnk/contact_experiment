# Deepskin 个性化 TCN 正式本地运行版

正式运行模型为 `models/deepskin_temporal_tcn_adapted_v1/`。该模型针对当前操作者的自然 PAT/RUB 动作进行了适配，并经操作者现场体验确认后，于 2026-08-24 提升为正式本地使用版本。

直接运行：

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\temporal_stream_gui.py
```

无参数启动现在默认加载正式适配模型。仍可使用 `--model-dir` 明确回放旧版本，例如：

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\temporal_stream_gui.py --model-dir .\models\deepskin_temporal_tcn_v1
```

正式模型使用 315 条 Gold 数据和 20 条自然 PAT/RUB 适配训练数据；8 条冻结开发验证全部正确。该验证来自当前操作者，不能解释为跨操作者或广泛人群准确率。TCN 的 softmax 阈值仍不是经过开放集校准的未知动作拒绝器。

旧 V1、旧 TCN、motion-v2 失败实验和候选包均保留，用于追溯和回滚。

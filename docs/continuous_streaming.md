# Deepskin 连续流式识别

## 图形界面（推荐调试方式）

在项目根目录运行：

```powershell
python .\scripts\stream_recognize_gui.py
```

点击“启动连续识别”后，SDK 和设备会一直保持开启并连续采样，直到点击“停止”或关闭窗口。每个触摸事件在完全抬手、结束保持时间达到 550 ms 后进行一次最终分类。该值用于聚合 PAT 的 2～4 次相邻轻拍。

界面中的“阈值倍率”控制正类门控：

- `1.20`：当前运行默认值；有效阈值为校准阈值的 1.2 倍。
- `1.00`：模型校准得到的原始阈值。
- 小于 `1.00`：更严格，误输出更少，但可能漏掉更多目标动作。
- 大于 `1.00`：更宽松，目标动作更容易输出，但无效动作误输出风险增加。

界面同时显示候选类别、门控距离、原始阈值、倍率、有效阈值以及接受/抑制结果。修改倍率后，从下一个完整事件起生效。默认不保存原始事件，避免产生冗余数据。

## 命令行流式接口

```powershell
python -u .\scripts\stream_recognize.py
```

标准输出只产生通过门控的最终目标动作，每行一个 JSON 对象。低置信度事件写入标准错误并标记为 `SUPPRESSED_LOW_CONFIDENCE`，不会伪装成目标手势。

只输出标签：

```powershell
python -u .\scripts\stream_recognize.py --output-format label
```

临时恢复原始校准门控：

```powershell
python -u .\scripts\stream_recognize.py --gate-threshold-scale 1.0
```

旋转电子皮肤 180°：

```powershell
python -u .\scripts\stream_recognize.py --orientation rotate_180
```

按 `Ctrl+C` 停止。仅在明确需要诊断数据时使用 `--save-events-dir <目录>`；默认不会保存每次触摸的原始矩阵。

## 当前输出时机

当前版本输出的是“事件结束后的最终结果”，不是触摸过程中的逐帧猜测。这样可以聚合相隔较近的多次脉冲，并避免 TAP、PAT、POKE 等尚未完成时过早输出错误类别。

当前推荐参数：起始阈值 `3.0`、基线余量 `2.0`、开始防抖 `40 ms`、结束保持 `550 ms`、门控倍率 `1.20`。执行 PAT 时，应在同一区域用较大接触面轻拍 2～4 次，每次明显卸力，相邻间隔控制在约 0.5 秒以内。

PAT 使用 episode 级规则：如果模型首先给出 IMPACT，但完整事件包含 2～4 个持续至少 40 ms、相隔至少 100 ms 的接触脉冲，最终结果修正为 PAT。GUI 会同时显示原始模型候选、修正结果和有效脉冲数；短暂传感器回弹不会被当成第二次轻拍。

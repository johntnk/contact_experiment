# TCN 实验版连续识别

运行：

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\temporal_stream_gui.py
```

该入口与 V1 RBF-SVM GUI 完全分离，不覆盖 V1 模型。点击“启动 TCN 连续识别”后设备持续采样，直到点击“停止”。

默认置信度阈值为 `0.50`：低于阈值的事件显示“已忽略”。该阈值仅供体验调试，尚未像 V1 正类距离门控一样完成开放集校准；神经网络 softmax 概率不能直接解释为真实正确率。

固定事件参数为：起始阈值 3.0、基线余量 2.0、开始防抖 40 ms、结束保持 550 ms、预滚动 150 ms。结果通常在最后一次抬手约 0.6 秒后出现。

已知取舍：三折 OOF Macro F1 为 0.8623；动态类别整体表现较好，但 STATIC_TOUCH 明显弱于 V1。该 GUI 用于现场体验和诊断，不是正式发布替换。

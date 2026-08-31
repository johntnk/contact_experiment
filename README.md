# Deepskin Social Touch Agent

基于 Deepskin 18×29 电容阵列、个性化 TCN、IM Agent SSE 和远程情绪 TTS 的 Windows 实时社交触摸系统。

当前完整链路：

```text
Deepskin USB → 触摸事件检测 → TCN 七分类 → 3 秒背压 → IM Agent SSE
             → Agent 回复 → 远程 TTS → 本机 WAV 播放
```

## 功能

- 七类触摸：`STATIC_TOUCH`、`STROKE`、`RUB`、`TAP`、`POKE`、`PAT`、`IMPACT`
- RUB、STATIC_TOUCH、STROKE 使用因果滑动窗口持续输出
- TAP、POKE、IMPACT、PAT 在完整事件结束后判定
- Agent 请求与硬件采样完全分离；任意时刻一个请求在途，积压时只保留最新动作
- 远程 TTS 支持情绪字段、最新回复中断旧播放，以及 GUI 单次音量 0–100
- GPU 可用时自动使用 CUDA；否则使用 CPU

## 当前服务配置

- Agent 前端：`http://192.168.100.110:5175/`
- IM API：`http://192.168.100.110:5175/api/agent/im/generate`
- 远程 TTS：`http://192.168.102.106:8021/v1/tts`
- 默认用户：`test-user-1`
- 默认会话：`web-2026-08-24-5pj76na4`
- Agent 最短发送间隔：3 秒
- TTS 默认情绪：`excited_high`

这些参数均可通过命令行覆盖。

## 环境要求

- Windows 10/11 x64
- Python 3.12
- Deepskin 设备通过 USB 连接
- 可选 NVIDIA GPU；当前依赖使用 PyTorch CUDA 12.8 构建
- Agent 和 TTS 内网服务可达

## SDK 二进制

仓库保留供应商 SDK 的头文件、示例和说明，但闭源 DLL 因未发现公开再分发许可证，不随 GitHub 提交。运行前请从已获许可的 Deepskin SDK 包复制：

```text
DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll
DeepskinSDK_Distribution_cpp_x64/bin/HIDdAPI.dll
```

程序要求 x64 DLL，并会验证传感器矩阵为 18×29。

## 安装

```powershell
git clone https://github.com/johntnk/contact_experiment.git
cd contact_experiment
python -m venv .venv-temporal
.\.venv-temporal\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-temporal.txt
```

正式模型随仓库提供：

```text
models/deepskin_temporal_tcn_adapted_v1/model.pt
SHA-256: 804efe1f528cb4df81051d5188583f7a8c31169cd6ddf540d79a5540d7d063c5
```

## 运行完整服务

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\realtime_agent_remote_tts_gui.py
```

示例：覆盖网络配置和发送间隔：

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\realtime_agent_remote_tts_gui.py `
  --api-url http://192.168.100.110:5175/api/agent/im/generate `
  --frontend-url http://192.168.100.110:5175/ `
  --user-id test-user-1 `
  --session-id web-2026-08-24-5pj76na4 `
  --send-interval-s 3 `
  --tts-url http://192.168.102.106:8021/v1/tts `
  --tts-emotion excited_high
```

GUI 中点击“启动实时识别”。远程 TTS 窗口可调整情绪、音量并试听。

## 独立入口

- 仅实时识别：`scripts/realtime_stream_gui.py`
- 实时识别 + Agent：`scripts/realtime_agent_gui.py`
- 完整 Agent + 远程 TTS：`scripts/realtime_agent_remote_tts_gui.py`

Windows 本地 SAPI TTS 已退役，不再包含在项目中。

## 测试

```powershell
.\.venv-temporal\Scripts\python.exe -m unittest discover -s tests -q
```

发布前完整测试为 47 项。接口探测脚本：

```powershell
.\.venv-temporal\Scripts\python.exe .\scripts\probe_agent_sse.py `
  --url http://192.168.100.110:5175/api/agent/im/generate `
  --user-id test-user-1 `
  --session-id web-2026-08-24-5pj76na4
```

## 版本与数据边界

- 正式模型是同一操作者的个性化版本；不能据此声称对广泛人群具有相同准确率。
- 当前 TCN 的软最大值阈值不是经过开放集严格校准的拒绝模型。
- 原始 Gold 数据、CoST 数据、个性化录制和本地日志不随运行仓库提交。
- 实验过程与已知问题见 `experiment_ledger.md` 和 `memory/known_errors.md`。
- Agent/TTS 接入说明见 `docs/agent_im_bridge_v1.md` 与 `docs/remote_tts_runtime_v1.md`。

## 项目结构

```text
models/deepskin_temporal_tcn_adapted_v1/  正式 TCN 模型包
scripts/realtime_agent_remote_tts_gui.py  完整运行入口
src/deepskin_temporal/                    时序特征与 TCN
src/deepskin_agent/                       SSE 客户端与背压
src/deepskin_tts/                         远程 WAV 合成与播放
tests/                                    单元测试
docs/                                     运行及研究记录
```

本仓库未附加新的开源许可证；供应商 SDK 和第三方数据仍受各自许可约束。

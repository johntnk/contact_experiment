# Deepskin 社交触摸 V1 仓库审计

- 审计日期：2026-08-20
- 方案：`docs/deepskin_social_touch_7class_cost_plan_v3_1.md`
- 审计分支：`main`
- 基线提交：`6b2e91963c914ed2196e5c3643452a770a4a40eb`
- 阶段：V3.1 阶段 0

## 1. 结论

当前仓库满足进入阶段 1（SDK Runtime Probe）的条件：x64 SDK 提供公开矩阵读取 API，Python 3.12 x64 可以加载 SDK，设备曾成功完成初始化和采集启动，闭源组件无需修改或逆向。

当前仓库是 SDK 二进制分发包与示例集合，不是 SDK 内部实现源码。七分类系统应作为外部 Python 模块，通过 `deepskin_get_diff_matrix()` 获取矩阵。

## 2. 仓库结构

```text
Development_Board/
├── DeepskinSDK_Distribution_cpp_x64/  # x64 SDK、头文件、导入库与示例
├── DeepskinSDK_Distribution_cpp_x86/  # x86 SDK、头文件、导入库与示例
├── DeepskinSDK_TestPython/            # Python ctypes 示例和实验 GUI
├── Tool/                              # 闭源显示/录制工具与历史 CSV
├── DeepskinSDK_x64.sln
├── DeepskinSDK_x86.sln
├── Directory.Build.props
├── Directory.Build.targets
└── docs/
```

V1 主路径固定为 Python x64；x86 仅保留作供应商分发参考，不进入生产实验链路。

## 3. 运行环境

| 项目 | 审计结果 |
|---|---|
| 操作系统 | Windows 11，build 26200 |
| Python | 3.12.10，64-bit AMD64 |
| GPU | NVIDIA GeForce RTX 5060 Ti |
| GPU 显存 | 8151 MiB |
| NVIDIA 驱动 | 610.74 |
| Compute Capability | 12.0 |
| Git 分支 | `main`，跟踪 `origin/main` |

GPU 当前只记录为可用资源。V1 首轮 RBF-SVM、Random Forest 与 CPU 特征工程默认不依赖 GPU；只有后续明确引入支持 CUDA 的实验时才启用并单独验证环境。

已安装 Python 依赖：

```text
numpy
```

阶段 2 之前需要建立并安装版本固定的依赖，至少包括：

```text
scipy
pandas
scikit-learn
PyYAML
joblib
matplotlib
pyarrow
pytest
```

## 4. SDK 文件与边界

x64 运行依赖：

```text
DeepskinSDK_Distribution_cpp_x64/bin/DeepskinSDK.dll
DeepskinSDK_Distribution_cpp_x64/bin/HIDdAPI.dll
```

编译依赖：

```text
DeepskinSDK_Distribution_cpp_x64/include/deepskin_sensor.h
DeepskinSDK_Distribution_cpp_x64/include/deepskin_types.h
DeepskinSDK_Distribution_cpp_x64/lib/DeepskinSDK.lib
```

`DeepskinSDK.dll` 未签名；`HIDdAPI.dll` 的 Authenticode 签名有效。主机 Smart App Control 已由用户关闭，SDK 随后成功加载并进入手势采集循环。

下列组件是闭源二进制，不修改、不逆向、不反编译：

```text
DeepskinSDK.dll
HIDdAPI.dll
Demo_PCAPReportRawImage.exe
```

`.lib` 是 MSVC 导入库，`.pdb` 是调试符号，均不等同于 SDK 实现源码。

## 5. 公开 API 审计

来源：`include/deepskin_sensor.h`、`include/deepskin_types.h`、C++ 示例和随附使用说明。

### 5.1 控制 API

```c
int  deepskin_init(void);
void deepskin_release(void);
int  deepskin_enable(void);
void deepskin_disable(void);
void deepskin_reset(void);
```

- `deepskin_init()` 必须先调用；成功返回 `0`。
- `deepskin_enable()` 启动后台采集；成功返回 `0`。
- 正常清理顺序为 `deepskin_disable()` 后 `deepskin_release()`。
- `deepskin_reset()` 清除手势历史、重置滤波状态并重新校准基线。

### 5.2 矩阵与状态 API

```c
int deepskin_get_diff_matrix(double* out_data, int out_len);
int deepskin_is_touching(void);
int deepskin_get_matrix_size(int* tx, int* rx);
```

- 当前设备矩阵为 `tx=18`、`rx=29`。
- 矩阵按 row-major 存储：`data[row * rx + col]`。
- `out_data` 由调用方分配，`out_len` 必须至少为 `tx * rx`（当前 522）。
- 差分值为无物理单位的 `double`；正值通常代表压力变化，空闲时可能包含负值噪声。
- `deepskin_is_touching()` 返回 `1/0`。
- 公开 API 没有硬件帧序号、硬件时间戳、帧队列或丢帧计数。

因此阶段 1 只能测量“主机观测更新率、轮询间隔和重复矩阵比例”，不能声称精确测得硬件丢帧。Recorder 的时间戳应使用主机单调时钟，`frame_id` 是主机生成序号。

### 5.3 手势与 JSON API

```c
int deepskin_get_current_json(char* out_json, int buf_size);
int deepskin_get_gesture(DeepskinGesture* gesture);
int deepskin_get_all_gestures_json(char* out_json, int buf_size);
int deepskin_get_recent_gestures_json(int count, char* out_json, int buf_size);
```

- `deepskin_get_gesture()` 返回 `1` 表示出现一个新的完整手势，返回 `0` 表示没有新手势。
- JSON 缓冲区由调用方分配；缓冲不足返回 `DEEPSKIN_ERR_BUFFER_SMALL`。
- 随附文档建议 `current_json=1024`、`recent_json=8192`、`all_json=32768`，V1 应以返回码为准并配置上限。
- SDK 手势在动作结束后产生，和自研事件边界不保证一一对应。
- `DeepskinGesture.gesture_name` 是 `const char*`，其所有权和有效期未在公开头文件中声明；调用方不得释放或长期持有该指针。

### 5.4 错误 API 与错误码

```c
const char* deepskin_get_last_error(void);
```

```text
 0  DEEPSKIN_OK
-1  DEEPSKIN_ERR_NOT_FOUND
-2  DEEPSKIN_ERR_OPEN_FAILED
-3  DEEPSKIN_ERR_NOT_STARTED
-4  DEEPSKIN_ERR_BUFFER_SMALL
```

错误字符串由 SDK 所有，公开资料未说明跨线程有效期。包装层应在失败现场立即复制字符串。

## 6. 已有示例

| 文件 | 功能 | 可复用性 |
|---|---|---|
| `test_gesture.cpp` | 初始化并轮询旧六分类 | API 行为参考 |
| `test_json.cpp` | 获取最近手势 JSON | JSON 缓冲参考 |
| `test_matrix.cpp` | 读取并显示矩阵 | 行列布局参考 |
| `read_gesture.py` | Python ctypes 手势读取 | ctypes 结构参考 |
| `read_gesture_json.py` | Python JSON 示例 | 需改善裸缓冲结构用法 |
| `read_diff_matrix_sdk.py` | Python 实时矩阵显示 | 矩阵读取参考 |
| `deepskin_gui.py` | 实验性二维热图 GUI | 已通过语法检查，尚未纳入 V1 门控验证 |

现有 Python 示例有中文注释编码乱码、退出清理不统一、部分返回值未检查等问题。阶段 1 应新增独立、最小的 SDK wrapper/probe，不在原示例上堆叠训练逻辑。

## 7. 旧 SDK 六分类

```text
PalmPress
Slap
Stroke
FistSmash
FingerGather
SingleTap
```

这些结果只能用于调试对照或后续可选 legacy 特征，不得作为七分类 Gold 标签。

## 8. Tool 与历史数据

`Tool/Demo_PCAPReportRawImage.exe` 是闭源 GUI，能够注册/启用设备、显示二维矩阵和 3D Surface、设置显示阈值、录制 CSV、显示旧手势及 JSON。

Tool 目录只有 `HIDdAPI.dll`，没有 Tool 源码。不能修改其录制 schema 或内部算法。

### 8.1 CSV 汇总

| 文件 | 帧数 | 末帧时间 ms | 估算主机观测率 Hz | 阈值 |
|---|---:|---:|---:|---:|
| `recording_20260713_183015.csv` | 111 | 2,312 | 47.58 | 5 |
| `recording_20260721_114009.csv` | 58,335 | 1,225,641 | 47.59 | 5 |
| `recording_20260724_122127.csv` | 5,572 | 117,031 | 47.60 | 5 |
| `recording_20260820_120445.csv` | 19,841 | 376,985 | 52.63 | 10 |

总计 83,859 帧。每帧为 18 行、每行 29 个整数，帧头包含主机毫秒时间。数据存在 `-1/-2` 等负值。

CSV 不包含动作标签、操作者、规范 session、试验条件或事件边界，只能用于解析、回放、噪声/漂移分析、事件切分调试和性能测试。

## 9. 与 V3.1 方案不一致或需收紧的事实

1. SDK 无硬件时间戳和序列号，不能精确测量硬件丢帧。
2. 315 个 Gold 事件仅作为三操作者先导数据，不支持广泛人群泛化声明。
3. 第一轮实验收缩为 RBF-SVM/Random Forest、F0/F1、E0/E1/E2；E3/E4/F2 后置。
4. CoST 标签过滤暂定，必须保留过滤前后版本和人工抽查入口。
5. V1 过程中只输出接触状态；手势只在 episode 结束后给出最终分类。
6. CoST 使用许可已由项目负责人确认。
7. CoST 未产生稳定目标域收益时，发布 target-only 模型。
8. 当前训练依赖尚未建立和固定。

## 10. 版本与数据管理

- GitHub：`https://github.com/johntnk/contact_experiment.git`
- 原始 DLL/EXE/LIB、录制 CSV、原始/外部数据和模型权重已由 `.gitignore` 排除。
- 文档、配置、清单、指标和模型卡允许纳入版本管理。
- CoST 原始数据不得提交到 Git。
- 每阶段使用独立提交；阶段报告记录分支、提交、配置、随机种子、命令和产物路径。

## 11. 阶段 1 可执行入口

阶段 1 应新增 `scripts/probe_sdk.py` 与最小 SDK wrapper，执行：

1. 校验 Python/DLL 均为 x64。
2. 初始化、读取矩阵尺寸、启用采集。
3. 使用单调时钟连续采样一段可配置时长。
4. 记录主机轮询间隔、矩阵变化率、重复帧比例、负值噪声、touch state 和 SDK JSON 返回情况。
5. 用四角触摸人工确认行列、转置和镜像。
6. 无论成功或异常均执行 disable/release。
7. 不把主机生成的 frame id 描述为硬件序号。

## 12. 仍依赖硬件或项目负责人的事项

- 18×29 矩阵对应的实际物理尺寸和 taxel 间距。
- 矩阵相对皮肤实物的方向、镜像和原点。
- SDK/固件精确版本及硬件扫描频率。
- 压力量程、饱和值、线性度、迟滞和温漂规格。
- 三名操作者的安排和采集同意。
- CoST 原始文件在阶段 4 的本地可用性及实际校验和。
- 七类动作在当前硬件上的真实跨人可分性。

## 13. 阶段 0 门控

| 门控 | 状态 |
|---|---|
| 可定位公开矩阵读取 API | 通过 |
| 可确定 x64 运行依赖 | 通过 |
| 不需要逆向闭源组件 | 通过 |
| 已明确阶段 1 入口 | 通过 |

阶段 0 可以关闭，允许进入阶段 1。

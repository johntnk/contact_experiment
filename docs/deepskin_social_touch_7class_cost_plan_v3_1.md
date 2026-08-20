# Deepskin 数字皮肤社交触摸七分类：小样本与 CoST 数据复用 Codex 执行方案（V3.1）

> 文档用途：直接交给 Codex，在现有 Deepskin Windows SDK 分发仓库中分阶段实施。  
> 文档版本：V3.1  
> 日期：2026-08-20  
> 目标平台：Windows 10/11，x64  
> 目标硬件：Deepskin 单块矩形数字皮肤，18×29 二维差分压力矩阵，约 48～53 Hz  
> 监督数据方案：方案 B，3 名操作者 × 7 类 × 每类 15 次，共 315 个 Gold 事件  
> 第一版输出类别：`TAP`、`POKE`、`STATIC_TOUCH`、`STROKE`、`RUB`、`PAT`、`IMPACT`  
> CoST 定位：项目负责人已确认用途符合许可证；原始数据作为正式源域数据进入七类映射、源域训练和迁移实验

---

# 0. 给 Codex 的执行总指令

将本文放入仓库，例如：

```text
docs/deepskin_social_touch_7class_cost_plan_v3_1.md
```

在仓库根目录对 Codex 输入：

```text
请完整阅读 docs/deepskin_social_touch_7class_cost_plan_v3_1.md，并严格按照阶段门控顺序执行。

强制约束：
1. 不修改、不逆向、不反编译 DeepskinSDK.dll、HIDdAPI.dll、Demo_PCAPReportRawImage.exe。
2. V1 仅识别七个核心手势：TAP、POKE、STATIC_TOUCH、STROKE、RUB、PAT、IMPACT。
3. 不增加 UNKNOWN 训练类别，不采集 UNKNOWN 数据，不把 NO_CONTACT 当作手势类别。
4. 采用方案 B：3 名操作者 × 7 类 × 每类 15 次，共 315 个经人工确认的 Gold 事件。
5. 原 SDK 六分类只能作为对照、辅助特征或弱信息，不能作为目标七分类的 ground truth。
6. 项目负责人已确认当前用途符合 CoST 的 CC BY-NC-SA 4.0 许可。CoST 原始数据必须作为源域数据完成导入、校验、七类映射和迁移实验；不得跳过来源、署名和许可证记录。
7. 所有模型选择和参数搜索必须按 operator_id 分组，禁止随机按帧或事件混合切分。
8. 在 Gold 数据未完成前，不报告正式七分类分数；不得伪造硬件、数据或评估结果。
9. 每完成一个阶段，运行测试并更新 docs/progress_v1.md、docs/decisions_v1.md 和 artifacts/stage_reports/。
10. CoST 不得直接替代 Deepskin Gold 测试；所有迁移方案必须在相同的外层 Deepskin 操作者折上与 target-only 基线比较。
11. 首先只执行阶段 0。阶段 0 完成后按门控进入下一阶段。
```

---

# 1. 冻结的业务与技术决策

以下决策在 V3 中冻结。Codex 不得自行改变。

## 1.1 分类范围

分类器只学习以下七类：

```text
TAP
POKE
STATIC_TOUCH
STROKE
RUB
PAT
IMPACT
```

不属于 V1 分类范围：

```text
UNKNOWN
NO_CONTACT
MASSAGE
TICKLE
SCRATCH
FINGER_GATHER
GRAB
SQUEEZE
PINCH
PULL
TWIST
SHAKE
HUG
HANDSHAKE
```

说明：

- `NO_CONTACT` 是接触状态，不是训练类别。
- 本方案不训练 `UNKNOWN`，也不以 UNKNOWN 作为模型输出。
- 运行时若事件置信度不足，可以在内部标记为 `SUPPRESSED_LOW_CONFIDENCE` 并不向下游发出手势；该状态不是一个手势类别。
- 下游一旦收到手势名称，该名称必须是上述七类之一。

## 1.2 数据规模

采用方案 B：

```text
3 名操作者
× 7 类手势
× 每类 15 次
= 315 个 Gold 手势事件
```

每名操作者分 3 个独立 session 采集：

```text
每个 session：7 类 × 每类 5 次 = 35 个事件
每名操作者：3 session × 35 = 105 个事件
总计：3 人 × 105 = 315 个事件
```

独立 session 至少满足：

- 重新初始化设备和采集程序；
- 重新执行空闲基线采集；
- 使用新的 `session_id`；
- 最好在不同时间段采集，避免一次连续录制代表全部数据。

## 1.3 CoST 使用决策

项目负责人已于 2026-08-20 确认：当前项目用途符合 CoST 数据集的 `CC BY-NC-SA 4.0` 许可条件。

V3.1 冻结以下配置：

```text
cost.enabled = true
cost.usage_mode = research_data
cost.final_model_candidate_allowed = true
```

含义：

- 不再使用 `methods_only` 作为默认模式；
- 必须导入并校验 CoST 原始数据；
- 必须把 CoST 映射为本项目七类源域数据；
- 必须执行 source-only、target-only 和迁移训练对照；
- CoST 数据、源模型输出或联合训练结果允许进入最终模型候选；
- 最终是否采用 CoST 迁移方案，只由 Deepskin Gold 的严格外层操作者评估决定；
- 即使 CoST 没有提升目标域结果，也必须保留其复现实验、域偏移分析和失败结论。

必须保留以下许可与溯源信息：

```text
数据集名称
官方 DOI 和来源页面
许可证全文或许可证链接
下载/导入时间
原始文件校验和
本项目标签映射与过滤版本
使用 CoST 的模型和实验编号
所需署名信息
```

创建：

```text
docs/cost_usage_record.md
artifacts/cost/cost_provenance.json
```

CoST 原始文件仍不得提交到 Git；这是数据管理约束，不是禁止使用。

## 1.4 实现边界

本方案包含：

- 通过公开 SDK API 读取 18×29 差分矩阵；
- 受控采集和 trial 级人工确认；
- 接触事件切分；
- CoST-inspired 特征提取；
- 七分类训练、分组评估和模型选择；
- CoST 源域训练、域偏移分析与迁移实验；
- 流式 `START / UPDATE / END` 识别输出；
- 模型、配置、特征和报告版本管理。

本方案不包含：

- AI 对触觉的社交回应逻辑；
- 修改现有业务接口程序；
- 修改闭源 SDK 内部手势算法；
- 逆向 Tool 或 HID 协议；
- 压力值换算为牛顿或帕斯卡；
- x86 生产链路；
- V1 之外的新手势类别。

---

# 2. 已确认的项目事实

## 2.1 仓库与运行环境

```text
Development_Board/
├── DeepskinSDK_Distribution_cpp_x64/
├── DeepskinSDK_Distribution_cpp_x86/
├── DeepskinSDK_TestPython/
├── Tool/
├── DeepskinSDK_x64.sln
└── DeepskinSDK_x86.sln
```

已知环境：

```text
操作系统：Windows 10/11
主开发工具：Visual Studio、MSVC
Python：3.12 x64
Python 调用方式：ctypes.WinDLL
SDK 主库：DeepskinSDK.dll
SDK 导入库：DeepskinSDK.lib
底层通信库：HIDdAPI.dll
```

V1 主路径：

```text
Python 3.12 x64：采集、数据处理、特征、训练、评估和快速迭代
C++ x64：用于 API 行为对照和必要的最小运行探针
```

## 2.2 硬件输入

```text
矩阵：18 × 29
单帧 taxel：522
采样率：约 47.6～52.6 Hz
数组布局：row-major
索引：matrix[row * 29 + col]
数值：差分值，无已知物理单位
```

已知现象：

- 空闲值不一定为 0；
- 可能出现 `-1`、`-2` 等负值基线噪声；
- 可能存在漂移、迟滞和会话间尺度变化；
- 当前没有量程、线性度、温漂和物理标定信息。

## 2.3 可用 SDK 接口

设备控制：

```text
deepskin_init()
deepskin_release()
deepskin_enable()
deepskin_disable()
deepskin_reset()
```

数据读取：

```text
deepskin_get_diff_matrix()
deepskin_get_current_json()
deepskin_get_gesture()
deepskin_get_all_gestures_json()
deepskin_get_recent_gestures_json()
```

状态与错误：

```text
deepskin_is_touching()
deepskin_get_matrix_size()
deepskin_get_last_error()
```

## 2.4 SDK 原六分类

```text
PalmPress
Slap
Stroke
FistSmash
FingerGather
SingleTap
```

原 SDK 结果及 JSON 可以作为：

- 调试对照；
- 数据采集时的辅助显示；
- 模型输入的可选辅助特征；
- 消融实验中的 legacy 信息源。

禁止用途：

- 自动生成七分类 Gold 标签；
- 把 `SingleTap` 直接视为 `TAP` 或 `POKE`；
- 把 `Slap`、`FistSmash` 直接视为 `IMPACT` 真值；
- 自动补标既有无标签 CSV。

## 2.5 既有无标签 CSV

现有约 83,859 帧、18×29、约 48～53 Hz 的 CSV 没有动作标签、操作者和事件边界。

允许用途：

- 解析和回放；
- 基线噪声、漂移和坏点分析；
- 接触事件切分调试；
- 特征计算性能测试；
- 采集格式迁移测试。

禁止用途：

- 七分类监督训练；
- 正式准确率报告；
- 自动真实标签生成；
- 跨操作者评估。

---

# 3. 七类手势的操作性定义

数据采集、训练和评估必须使用统一定义。标签由“指令动作 + 操作者确认”产生，而不是由 SDK 旧分类产生。

## 3.1 `TAP`

定义：

- 单次、小面积、短时点触；
- 使用一个手指或少量指尖；
- 接触后快速离开；
- 质心移动很小；
- 不包含连续多次点触。

排除：

- 明显用力向内戳：归 `POKE`；
- 大面积多次拍击：归 `PAT`；
- 强冲击：归 `IMPACT`。

## 3.2 `POKE`

定义：

- 单次、小面积、明确向内施压；
- 压力上升通常比 TAP 更陡；
- 单位接触面积的相对峰值通常更高；
- 接触中心移动很小。

说明：

- `TAP` 与 `POKE` 是预期最难区分的类别之一；
- 不允许仅凭执行意图判断可分性，必须以目标域数据结果为准；
- V1 保持七类，不得擅自合并；若混淆严重，报告并请求项目负责人决策。

## 3.3 `STATIC_TOUCH`

定义：

- 接触持续存在；
- 质心位移小、轨迹长度短；
- 可以是指尖按住或手掌轻放；
- 压力可轻、中、较强，但不存在明显滑动或重复拍击。

## 3.4 `STROKE`

定义：

- 持续接触；
- 质心沿主要方向平滑移动；
- 起点到终点位移明显；
- 方向一致性较高；
- 不出现完整往返。

## 3.5 `RUB`

定义：

- 持续接触；
- 质心出现往返运动；
- 至少完成一个明显的方向反转；
- 轨迹总长度明显大于起终点直线距离。

## 3.6 `PAT`

定义：

- 使用较大面积手部接触；
- 同一区域附近完成 2～4 个分离或近似分离的脉冲；
- 相邻脉冲间有明显卸载；
- 不是单次强冲击。

说明：

- 一个单次大面积接触不能自动标为 PAT；
- PAT 必须通过 episode 聚合多个 micro-contact。

## 3.7 `IMPACT`

定义：

- 单次快速冲击；
- 压力变化陡峭；
- 相对峰值、能量或冲量较高；
- 可以表现为大面积 `broad` 或集中式 `focused`，但 V1 统一输出 `IMPACT`。

安全要求：

- 不以损坏传感器为代价采集极端力度；
- 采集协议中使用“可重复、明显但安全”的相对强度，不定义物理力值。

---

# 4. 方案 B：315 个 Gold 事件采集设计

## 4.1 样本矩阵

```text
operator_01：3 sessions × 7 gestures × 5 trials = 105
operator_02：3 sessions × 7 gestures × 5 trials = 105
operator_03：3 sessions × 7 gestures × 5 trials = 105
总计：315
```

## 4.2 单个 trial 流程

```text
1. 显示目标手势、位置、速度/力度/方向等条件
2. 3 秒倒计时
3. 记录约 0.3 秒空闲前置帧
4. 操作者执行一次动作
5. 通过 touch state 和矩阵自动检测事件结束
6. 记录约 0.5 秒空闲后置帧
7. 操作者选择 VALID / REDO / UNCERTAIN
8. VALID 才进入 Gold 清单；REDO 重新采集；UNCERTAIN 不进入训练
```

按约 50 Hz 估算：

```text
前置帧：约 15 帧
后置帧：约 25 帧
```

实际保存按时间戳，不写死帧数。

## 4.3 采集变化设计

315 个样本不追求完整笛卡尔积，但必须覆盖主要变化。Codex 应生成：

```text
protocol/gesture_variation_schedule.csv
```

要求每名操作者的每类 15 次中：

### 位置

至少覆盖：

```text
CENTER
LEFT
RIGHT
TOP
BOTTOM
```

每个位置约 3 次。

### 相对力度

至少覆盖：

```text
GENTLE
NORMAL
ROUGH
```

每种约 5 次。

### 速度

对动态动作至少覆盖：

```text
SLOW
NORMAL
FAST
```

每种约 5 次。

### 方向

对 `STROKE`、`RUB` 至少覆盖：

```text
LEFT_TO_RIGHT
RIGHT_TO_LEFT
TOP_TO_BOTTOM
BOTTOM_TO_TOP
```

尽量均衡。第五种可使用短距离对角线或重复一个较少出现的方向，但必须在 schedule 中明确。

### 类别特定变化

`TAP`：

- 五个位置；
- 三种相对力度；
- 单次接触。

`POKE`：

- 五个位置；
- 三种相对力度；
- 强调明确向内施压，不允许变成持续按住。

`STATIC_TOUCH`：

- 短、中、长三种持续时间；
- 指尖式和手掌式接触都要出现；
- 不移动。

`STROKE`：

- 四个主要方向；
- 慢、中、快三种速度；
- 覆盖短、中、长移动距离。

`RUB`：

- 1、2、3 个往返周期；
- 慢、中、快三种速度；
- 横向和纵向都要出现。

`PAT`：

- 2、3、4 个脉冲；
- 脉冲位置相近；
- 脉冲间隔覆盖慢、中、快节奏。

`IMPACT`：

- broad 与 focused 两种接触形态；
- 中等和较强但安全的相对强度；
- 保持单次冲击。

## 4.4 随机化

同一 session 内不得按照固定类别顺序连续采集全部样本。

Codex 应生成带固定随机种子的顺序表：

```text
protocol/session_orders/<operator_id>_<session_id>.csv
```

要求：

- 同类动作不超过 2 次连续出现；
- 每个 session 包含每类 5 次；
- 保存随机种子；
- 不覆盖已执行的历史 order 文件。

## 4.5 Gold 标签确认

每个 trial 保存：

```json
{
  "instruction_label": "STROKE",
  "verified_label": "STROKE",
  "trial_status": "VALID",
  "label_source": "CONTROLLED_CONFIRMED",
  "label_quality": "GOLD"
}
```

若执行错误：

```json
{
  "instruction_label": "STROKE",
  "verified_label": null,
  "trial_status": "REDO"
}
```

禁止把 `instruction_label` 自动视为有效标签，必须经过确认。

---

# 5. Canonical 数据格式

## 5.1 推荐目录

```text
data/
├── raw/
│   └── deepskin/
│       └── <operator_id>/<session_id>/<trial_id>/
│           ├── matrix.npz
│           ├── metadata.json
│           ├── sdk_events.jsonl
│           └── preview.png
├── external/
│   └── cost/                 # 可选；必须 gitignore
├── interim/
│   ├── segmented/
│   └── features/
├── processed/
│   └── manifests/
└── legacy_unlabeled/
```

原始 trial 文件不可覆盖。重新处理结果写入 `interim/` 或 `processed/`。

## 5.2 `matrix.npz`

必须包含：

```text
matrix          shape [T, 18, 29]
timestamps_ms   shape [T]
frame_ids       shape [T]
touch_state     shape [T]
```

可选：

```text
legacy_gesture_id_per_frame
sdk_sequence_no
```

## 5.3 `metadata.json`

至少包含：

```json
{
  "schema_version": "deepskin-trial-v1",
  "operator_id": "operator_01",
  "session_id": "session_01",
  "trial_id": "trial_000001",
  "instruction_label": "STROKE",
  "verified_label": "STROKE",
  "trial_status": "VALID",
  "label_quality": "GOLD",
  "intensity_instruction": "NORMAL",
  "speed_instruction": "SLOW",
  "direction_instruction": "LEFT_TO_RIGHT",
  "position_instruction": "CENTER",
  "contact_style_instruction": null,
  "pulse_count_instruction": null,
  "device_model": "Orion_0000_A0KZ",
  "matrix_rows": 18,
  "matrix_cols": 29,
  "sampling_rate_observed_hz": 50.1,
  "sdk_version": "unknown",
  "recorded_at": "2026-08-20T00:00:00+08:00",
  "notes": ""
}
```

## 5.4 Manifest

生成：

```text
data/processed/manifests/gold_manifest.csv
```

一行一个 trial，至少包含：

```text
trial_path
operator_id
session_id
trial_id
verified_label
trial_status
intensity_instruction
speed_instruction
direction_instruction
position_instruction
sampling_rate_observed_hz
frame_count
duration_ms
quality_flags
```

---

# 6. CoST 数据引入、七类映射与源域适配

## 6.1 官方数据事实

官方数据集：

```text
名称：Corpus of Social Touch (CoST)
版本：Version 1
DOI：10.4121/uuid:5ef62345-3b3e-479c-8e1d-c922748c9b29
样本数：7,805
类别数：14
变化：gentle / normal / rough
传感器：8×8 压力网格
采样率：135 Hz
许可证：CC BY-NC-SA 4.0
```

官方文件：

```text
README.txt
CoST.csv
```

官方页面当前记录的 MD5：

```text
README.txt  454a2f2e38470fcb6087c891a85db238
CoST.csv    c6035f76d1e13f81168dd79586dcb742
```

若官方文件版本或校验和发生变化，不得强行通过旧校验。应停止处理、记录实际来源和新校验和，并由项目负责人确认版本。

## 6.2 固定使用记录

创建：

```text
docs/cost_usage_record.md
```

内容至少包括：

```text
cost_usage_mode: research_data
approved_by: project_owner
approved_at: 2026-08-20
intended_use: Deepskin 七类社交触摸源域训练与迁移研究
license: CC BY-NC-SA 4.0
source_doi: 10.4121/uuid:5ef62345-3b3e-479c-8e1d-c922748c9b29
attribution_required: true
share_alike_tracking: true
final_model_candidate_allowed: true
notes:
```

同时创建机器可读文件：

```text
artifacts/cost/cost_provenance.json
```

任何使用 CoST 数据或派生源模型的实验，都必须在实验配置和模型卡中引用该 provenance 文件。

## 6.3 数据导入与完整性校验

实现：

```text
scripts/prepare_cost_7class.py
scripts/inspect_cost_schema.py
```

支持两种输入方式：

```text
1. 从项目负责人提供的本地 CoST 文件导入；
2. 从官方数据页面取得文件后导入。
```

要求：

- 原始文件保存到 `data/external/cost/raw/`；
- 处理结果保存到 `data/external/cost/processed/`；
- 两个目录均加入 `.gitignore`；
- 导入时计算 MD5 和 SHA-256；
- 验证列数、样本数、类别集合、参与者字段、时间序列长度和缺失值；
- 不覆盖已经校验过的原始文件；
- 所有转换都生成 manifest 和配置哈希。

输出：

```text
artifacts/cost/cost_schema_report.md
artifacts/cost/cost_checksums.json
artifacts/cost/cost_source_manifest.csv
```

## 6.4 CoST 七类映射

仅保留下列源标签：

```text
tap      -> TAP
poke     -> POKE
press    -> STATIC_TOUCH
stroke   -> STROKE
rub      -> RUB
pat      -> PAT
hit      -> IMPACT
slap     -> IMPACT
```

丢弃其他 CoST 类别：

```text
grab
massage
pinch
scratch
squeeze
tickle
```

`gentle / normal / rough` 保留为元数据，不作为七分类目标。

映射后必须保存：

```text
source_label
mapped_label
source_subject_id
source_intensity
source_sample_id
mapping_version
filter_status
filter_reason
```

## 6.5 标签兼容性过滤

CoST 原始采集没有严格限制一次 capture 中手势重复次数。为了对齐本项目定义，`cost_adapter` 必须先计算：

```text
pulse_count
complete_release_count
contact_area_ratio
trajectory_reversal_count
trajectory_straightness
```

推荐过滤规则：

- CoST `tap`：优先保留 `pulse_count == 1` 的样本；
- CoST `pat`：优先保留 `pulse_count >= 2` 且接触面积较大的样本；
- CoST `stroke`：优先保留方向一致、无完整往返的样本；
- CoST `rub`：优先保留至少一次明显方向反转的样本；
- CoST `hit` 与 `slap`：合并为 `IMPACT`，同时保留原标签作为属性；
- 无法确认兼容性的源样本标记为 `FILTERED_AMBIGUOUS`，不得强行加入训练。

过滤阈值只能来自：

```text
CoST 自身统计
明确的操作定义
Deepskin 外层训练操作者数据
```

禁止查看 Deepskin 外层测试操作者后调整过滤规则。

输出：

```text
artifacts/cost/cost_mapping_report.md
artifacts/cost/cost_class_counts_before_after.csv
artifacts/cost/cost_filter_config.yaml
```

## 6.6 跨传感器共享表示

V1 的 CoST 迁移只使用 `F0_common` 共享事件级特征：

- 空间坐标归一化到 `[0,1]`；
- 时间统一使用秒、毫秒和 Hz；
- 压力使用各数据域内的无量纲稳健归一化；
- 空间分布使用固定 `4×4` 区域池化；
- 不把 8×8 或 18×29 的原始行列长度直接作为共享特征；
- 不把 CoST 的绝对压力阈值复制到 Deepskin；
- 不强制把 135 Hz 原始序列插值成 50 Hz 后直接共训原始矩阵模型。

CoST 和 Deepskin 的源数据分别保留：

```text
source_dataset = COST | DEEPSKIN
domain_id = source | target
```

`domain_id` 用于采样、加权和报告，默认不得作为最终分类器输入特征。

## 6.7 使用边界

禁止：

- 把 CoST source-only 结果当作 Deepskin 真实性能；
- 把 CoST 8×8、135 Hz 的模型直接发布到 18×29、约 50 Hz 的运行时；
- 用 Deepskin 外层测试标签选择 CoST 映射、过滤、源权重或特征；
- 让数量更大的 CoST 样本未经权重控制地淹没 315 个 Deepskin Gold 样本；
- 删除 CoST 的来源、署名、许可证和派生实验记录；
- 把 CoST 原始文件提交到 Git。

# 7. 预处理与事件切分

## 7.1 基线校正

每个 session 和 trial 使用前置空闲帧估计基线：

```text
baseline[row, col] = median(pre_contact_frames)
noise_mad[row, col] = MAD(pre_contact_frames)
```

校正：

```text
corrected = raw_diff - baseline
```

默认保留原始正负值用于质量分析；用于接触和分类的分支可以：

```text
positive = max(corrected, 0)
```

不得删除原始数据。

## 7.2 接触阈值

阈值应结合：

```text
per-taxel noise threshold
session-level total pressure threshold
active taxel count
SDK deepskin_is_touching()
```

初始候选：

```text
taxel_threshold = median_idle + k * MAD_idle
```

`k` 必须配置化，并只使用训练 session 调整。

## 7.3 空间归一化

Deepskin 坐标：

```text
x_norm = col / 28
y_norm = row / 17
```

CoST 坐标：

```text
x_norm = col / 7
y_norm = row / 7
```

所有跨传感器共享轨迹特征必须使用归一化坐标。

## 7.4 时间归一化

所有时序量使用真实时间：

```text
duration_ms
speed_per_second
frequency_hz
pulse_interval_ms
```

不得把“帧数”作为跨设备共享的时间单位。

## 7.5 micro-contact 与 episode

第一层：micro-contact

```text
CONTACT_START
CONTACT_ACTIVE
CONTACT_END
```

第二层：episode 聚合

- 连续接触：通常形成一个 episode；
- PAT：多个相邻 micro-contact 聚合为一个 episode；
- episode gap 初值允许设置为 300～500 ms；
- 聚合同时检查质心距离和接触面积相似性；
- 最终参数由 Gold 训练 session 调整。

## 7.6 事件质量检查

为每个事件生成：

```text
TOO_SHORT
TOO_LONG
NO_ACTIVE_TAXEL
EXCESSIVE_DROPPED_FRAMES
NON_MONOTONIC_TIMESTAMP
BASELINE_UNSTABLE
MATRIX_SHAPE_ERROR
CONTACT_AT_RESET
```

Gold trial 有严重质量错误时，不进入训练，重新采集。

---

# 8. CoST-inspired 特征体系

创建：

```text
src/features/cost_inspired/
```

所有特征必须：

- 不写死 8×8；
- 不写死 135 Hz；
- 支持 `[T,H,W]`；
- 使用归一化空间和真实时间；
- 具有明确名称、单位、版本和测试。

## 8.1 `F0_common`：CoST 与 Deepskin 共享特征

### 压力统计

```text
mean_pressure
max_pressure
pressure_variability
pressure_variance
pressure_p50
pressure_p90
pressure_p95
pressure_p99
pressure_energy
pressure_impulse
```

### 固定空间池化

为了兼容 8×8 与 18×29，把传感器归一化到固定 `4×4` 区域，计算：

```text
region_mean_pressure_4x4
region_max_pressure_4x4
region_active_ratio_4x4
```

禁止把 8 行/8 列或 18 行/29 列特征作为跨域共享输入。

### 接触面积

```text
mean_contact_area_ratio
max_contact_area_ratio
area_at_max_total_pressure
area_variability
```

### 时间峰值与脉冲

```text
temporal_peak_count
positive_mean_crossing_count
pulse_count
complete_release_count
mean_pulse_interval_ms
pulse_interval_std_ms
```

### 质心与轨迹

```text
centroid_x_start
centroid_y_start
centroid_x_end
centroid_y_end
centroid_displacement
trajectory_length
mean_step_distance
sum_abs_dx
sum_abs_dy
trajectory_straightness
```

### 压力分布

对归一化压力使用 8-bin histogram：

```text
pressure_hist_bin_0 ... pressure_hist_bin_7
```

禁止复用 CoST 的绝对 `0～1023` bin。

### 空间峰值

```text
mean_spatial_peak_count
var_spatial_peak_count
mean_peak_to_centroid_distance
mean_peak_distance_change
```

### 空间/时间导数

```text
mean_abs_row_derivative
mean_abs_col_derivative
mean_abs_temporal_derivative
```

### 移动方向

```text
direction_quadrant_0_ratio
direction_quadrant_1_ratio
direction_quadrant_2_ratio
direction_quadrant_3_ratio
```

### 移动幅度

```text
movement_magnitude_mean
movement_magnitude_std
movement_magnitude_sum
movement_magnitude_range
```

### 周期性

```text
centroid_x_dominant_frequency_hz
centroid_y_dominant_frequency_hz
pressure_dominant_frequency_hz
periodicity_strength
```

## 8.2 `F1_deepskin_enhanced`：目标域增强特征

在 `F0_common` 基础上增加：

```text
rise_rate
fall_rate
peak_pressure_per_active_taxel
peak_pressure_per_area
contact_component_count_mean
contact_component_count_max
direction_reversal_count
direction_consistency
area_change_rate
pressure_area_correlation
bbox_width_norm
bbox_height_norm
bbox_aspect_ratio
compactness
spatial_dispersion
max_speed
mean_acceleration
trajectory_smoothness
```

## 8.3 `F2_deepskin_legacy`

在 `F1` 基础上增加原 SDK 可用字段，例如：

```text
legacy_gesture_id
legacy_duration
legacy_max_force
legacy_mean_force
legacy_force_energy
legacy_force_std
legacy_max_area
legacy_mean_area
legacy_displacement
legacy_speed
legacy_acceleration
legacy_aspect_ratio
legacy_diffusion
legacy_trajectory_stability
```

若某字段不是所有事件都可用：

- 增加 `<feature>_available` 标志；
- 使用训练 fold 内拟合的 imputer；
- 不得用测试 fold 的统计量填充。

## 8.4 特征版本

每个 feature table 必须保存：

```text
feature_schema_version
preprocess_config_hash
segment_config_hash
source_dataset
trial_id
operator_id
label
```

生成：

```text
artifacts/features/feature_dictionary.md
artifacts/features/feature_coverage_report.csv
```

---

# 9. 模型与训练实验

## 9.1 模型候选

### Baseline A：Legacy 对照

使用原 SDK 六分类做条件映射，仅用于对照：

```text
PalmPress -> STATIC_TOUCH
Stroke -> STROKE
Slap/FistSmash -> IMPACT
SingleTap -> TAP 或 POKE 无法确定
FingerGather -> 无对应
```

该基线不得成为最终模型。

### Baseline B：RBF-SVM

复用 CoST 原研究训练思想：

```text
feature scaling
RBF kernel
C / gamma 网格搜索
按操作者嵌套交叉验证
```

候选参数初始网格：

```text
C = 2^-5, 2^-3, ..., 2^15
gamma = 2^-15, 2^-13, ..., 2^3
```

可以先粗搜索后局部细化，但完整搜索空间和实际搜索结果必须记录。

### Baseline C：Extra Trees

候选参数：

```text
n_estimators: 300, 600
max_depth: null, 8, 16
min_samples_leaf: 1, 2, 4
max_features: sqrt, 0.5, 1.0
class_weight: balanced
```

### Baseline D：Random Forest

候选参数：

```text
n_estimators: 300, 600
max_depth: null, 8, 16
min_samples_leaf: 1, 2, 4
max_features: sqrt, 0.5, 1.0
class_weight: balanced
```

### 可选 Baseline E：分层混合模型

物理分流：

```text
single_impulse    -> TAP / POKE / IMPACT
repeated_impulse  -> PAT
static_contact    -> STATIC_TOUCH
moving_contact    -> STROKE / RUB
```

规则只做路由，不直接替代最终训练结果。是否保留该模型由目标域评估决定。

## 9.2 V1 不做的模型

V1 不实现：

```text
3D CNN
Transformer
大型 TCN
自监督基础模型
复杂域适配网络
```

只有在 315 个 Gold 基线完成、且传统模型明显不足后，才能另立 V2 方案。

## 9.3 特征实验矩阵

至少比较：

```text
F0_common
F1_deepskin_enhanced
F2_deepskin_legacy
```

模型矩阵：

```text
RBF-SVM × F0/F1/F2
Extra Trees × F0/F1/F2
Random Forest × F0/F1/F2
```

目标：回答原 SDK legacy 特征是否真正改善独立操作者性能。

---

# 10. 严格的分组评估

## 10.1 外层评估

采用 3-fold Leave-One-Operator-Out：

```text
Fold 1：operator_01 测试；operator_02 + operator_03 训练/验证
Fold 2：operator_02 测试；operator_01 + operator_03 训练/验证
Fold 3：operator_03 测试；operator_01 + operator_02 训练/验证
```

每名操作者只在一个外层测试 fold 中出现。

## 10.2 内层模型选择

在每个外层 fold 的两个训练操作者上，采用 2-fold group validation：

```text
inner-A：训练操作者 X，验证操作者 Y
inner-B：训练操作者 Y，验证操作者 X
```

使用两个 inner fold 的平均 Macro F1 选择超参数。

选择完成后，在两个训练操作者的全部数据上重新训练，再评估外层测试操作者。

## 10.3 防止泄漏

以下对象必须留在同一 fold：

- 同一 `trial_id` 的全部帧；
- 同一 trial 的所有时间前缀；
- 同一 trial 的增强版本；
- 同一 operator 的所有 session；
- 同一事件派生出的全部 feature rows。

所有步骤必须在训练 fold 内拟合：

```text
baseline aggregation
imputation
scaling
feature selection
class weighting
probability calibration
CoST/Deepskin domain transformation
```

## 10.4 指标

主要指标：

```text
Macro F1
Balanced Accuracy
```

必须报告：

```text
per-class precision
per-class recall
per-class F1
confusion matrix
accuracy
top-2 accuracy
每个 operator fold 的分数
三折均值和标准差
```

推荐目标，不构成保证：

```text
Macro F1 >= 0.80
Balanced Accuracy >= 0.80
每类 F1 >= 0.65
```

如果未达到：

- 不修改真实结果；
- 分析混淆和数据质量；
- 优先补采难类，不擅自增加类别或合并类别；
- 输出 `docs/model_gap_analysis.md`。

## 10.5 结果定位

只有 3 名操作者时，结果应描述为：

```text
三操作者先导跨操作者评估
```

不得宣称已经证明广泛人群泛化。

---

# 11. CoST 源域训练与迁移实验

本节为 V3.1 必做实验，不再以许可证开关决定是否执行。所有实验都必须使用完全相同的 Deepskin 外层 Leave-One-Operator-Out 测试折，保证可比较。

## 11.1 E0：Deepskin target-only

```text
训练：Deepskin Gold 外层训练操作者
验证：Deepskin Gold 内层验证操作者
测试：Deepskin Gold 外层测试操作者
```

这是最终比较基准，也是 CoST 没有产生目标域收益时的回退方案。

## 11.2 E1：CoST source-only 域偏移诊断

```text
训练：映射并过滤后的 CoST 七类
测试：Deepskin 外层测试操作者
```

要求：

- 仅使用 `F0_common`；
- 使用 CoST 参与者分组完成源域内部模型选择；
- 报告 CoST 内部结果和 Deepskin 跨域结果；
- 计算每类性能下降和混淆变化。

目的：量化传感器、采样率和动作定义造成的域偏移。

E1 永远不能单独成为最终模型。

## 11.3 E2：类别与域平衡的联合训练

只使用 `F0_common`，将 CoST 与当前外层 fold 的 Deepskin 训练操作者联合训练。

不能按原始样本数直接拼接。采用域归一化权重：

```text
每个域内部先按 mapped_label 做类别平衡；
Deepskin 域总权重归一化为 1.0；
CoST 域总权重乘以 alpha；
alpha 候选：0.05、0.10、0.25、0.50、1.00。
```

形式上：

```text
w_target(i) ∝ 1 / n_target_class(i)
w_source(i) ∝ alpha / n_source_class(i)
```

`alpha` 必须只通过 Deepskin 内层验证操作者选择。禁止用外层测试操作者选择。

至少比较：

```text
RBF-SVM + F0_common
Extra Trees + F0_common
Random Forest + F0_common
```

## 11.4 E3：CoST 源模型分数作为辅助特征

步骤：

```text
1. 在映射后的 CoST 上训练七类 source classifier；
2. 对 Deepskin 事件输出七类 probability 或 decision score；
3. 将 7 维 source score 加入 Deepskin F1 特征；
4. 最终分类器只使用当前外层 fold 的 Deepskin Gold 标签训练；
5. 在外层测试操作者上评估。
```

要求：

- 源模型不访问任何 Deepskin 标签；
- 目标模型的 scaler、imputer 和超参数只在目标训练操作者内拟合；
- 记录源模型对各 Deepskin 类别的校准偏差。

## 11.5 E4：CoST 辅助的共享特征选择

目的：利用较大的 CoST 数据判断哪些 `F0_common` 特征对七类动作具有稳定信息，但最终分类器仍可只在 Deepskin Gold 上训练。

流程：

```text
1. 在 CoST 参与者分组 CV 中计算 permutation importance 或稳定选择频率；
2. 形成若干候选共享特征子集；
3. 在 Deepskin 内层操作者验证中选择是否使用该子集；
4. 外层测试操作者只用于一次最终评估。
```

不得直接用 CoST 全数据和 Deepskin 外层测试共同做特征选择。

## 11.6 实验矩阵

每个外层 fold 至少完成：

```text
E0 target-only：F0 / F1 / F2
E1 source-only：F0
E2 joint weighted：F0 × alpha
E3 source-score assisted：F1 + 7 source scores
E4 source-informed feature subset：target-only classifier
```

保存：

```text
random_seed
outer_test_operator
inner_validation_operator
source_model_config
target_model_config
cost_mapping_version
cost_filter_config_hash
source_weight_alpha
feature_schema_version
```

## 11.7 CoST 迁移方案进入最终模型的门控

CoST 数据已经允许使用，但“允许使用”不等于“必须合入最终模型”。迁移方案只有同时满足以下条件，才可击败 E0 target-only 并进入发布候选：

```text
1. 三个外层 fold 中至少两个 fold 的 Macro F1 不低于 target-only；
2. 三折平均 Macro F1 至少提升 0.01，或在 Macro F1 持平时显著降低 operator fold 方差；
3. Balanced Accuracy 不下降超过 0.01；
4. 任一核心类别 F1 不下降超过 0.05；
5. 在至少三个固定随机种子下结论方向一致；
6. pooled out-of-fold 预测的配对 bootstrap 不显示明显负收益；
7. 模型包完整记录 CoST 来源、映射、过滤、权重和许可证信息。
```

若多个迁移方案通过门控，按以下优先级选择：

```text
1. Macro F1
2. 最低类别 F1
3. operator fold 方差
4. Balanced Accuracy
5. 推理复杂度
6. 可解释性
```

若没有迁移方案通过门控：

```text
最终发布 E0 target-only；
CoST 仍作为已完成的源域复现、特征验证和域偏移研究保留。
```

# 12. 最终模型训练与发布

## 12.1 模型选择

选择依据按优先级：

```text
1. 三折外层 Macro F1
2. Balanced Accuracy
3. 最低类别 F1
4. operator fold 方差
5. 推理延迟
6. 模型复杂度和可解释性
```

不得仅选择总体 accuracy 最高的模型。

## 12.2 最终训练

完成无偏外层评估并冻结模型方案后：

- 若 E0 target-only 胜出：使用全部 315 个 VALID Gold 事件训练发布模型；
- 若 E2/E3/E4 中的 CoST 迁移方案通过门控并胜出：按冻结的映射、过滤、源权重和模型结构，使用全部 315 个 Gold 事件及相应 CoST 源数据重新训练；
- 超参数和 source weight 只能来自嵌套 CV 的稳定结果；
- 不再用该全量模型声称新的测试性能；
- 发布报告仍引用外层三折 out-of-fold 结果；
- 最终模型必须注明 `training_recipe = target_only | cost_joint | cost_score_assisted | cost_feature_selected`。

## 12.3 模型包

```text
models/deepskin_social_touch_v1/
├── model.joblib
├── preprocess.joblib
├── feature_schema.json
├── label_map.json
├── model_card.md
├── training_manifest.csv
├── metrics.json
├── confusion_matrix.csv
├── config.yaml
├── cost_provenance.json
├── source_data_manifest.csv
└── checksums.txt
```

`label_map.json` 固定：

```json
{
  "0": "TAP",
  "1": "POKE",
  "2": "STATIC_TOUCH",
  "3": "STROKE",
  "4": "RUB",
  "5": "PAT",
  "6": "IMPACT"
}
```

---

# 13. 流式识别输出

本节只定义识别模块输出，不实现 AI 社交回应。

## 13.1 状态

```text
CONTACT_START
CONTACT_UPDATE
GESTURE_UPDATE
GESTURE_END
```

识别状态：

```text
PENDING
PROVISIONAL
FINAL
SUPPRESSED_LOW_CONFIDENCE
```

`SUPPRESSED_LOW_CONFIDENCE` 是内部状态，不是手势类别。

## 13.2 输出策略

- 内部按硬件实际采样率处理；
- 结构化 UPDATE 默认以 10 Hz 输出，可配置为 5～20 Hz；
- `GESTURE_UPDATE` 可以输出 provisional 七类候选；
- `GESTURE_END` 输出最终七类；
- 置信度低于阈值时可以不向下游发送最终手势，只写内部日志；
- 不输出 `UNKNOWN`。

## 13.3 推荐事件结构

```json
{
  "schema_version": "deepskin-social-touch-v1",
  "event_id": "evt_000123",
  "sequence_no": 12,
  "phase": "UPDATE",
  "recognition_state": "PROVISIONAL",
  "gesture": "STROKE",
  "confidence": 0.73,
  "final": false,
  "duration_ms": 420,
  "contact_area_ratio": 0.14,
  "centroid": [0.42, 0.61],
  "mean_pressure_normalized": 0.23,
  "peak_pressure_normalized": 0.31,
  "motion_speed": 0.08,
  "direction_reversal_count": 0,
  "model_version": "1.0.0"
}
```

最终事件：

```json
{
  "schema_version": "deepskin-social-touch-v1",
  "event_id": "evt_000123",
  "sequence_no": 28,
  "phase": "END",
  "recognition_state": "FINAL",
  "gesture": "STROKE",
  "confidence": 0.91,
  "final": true,
  "model_version": "1.0.0"
}
```

## 13.4 流式稳定性

实现：

```text
candidate smoothing
minimum dwell time
confidence hysteresis
top1-top2 margin
candidate switch threshold
final event idempotency
```

同一 `event_id`：

- `sequence_no` 单调递增；
- 最终事件最多发送一次；
- 最终标签发出后不可更改。

---

# 14. 推荐仓库结构

在不大规模破坏现有仓库的前提下，新增：

```text
config/
├── acquisition.yaml
├── preprocessing.yaml
├── segmentation.yaml
├── features.yaml
├── training.yaml
├── runtime.yaml
└── cost.yaml

docs/
├── deepskin_social_touch_7class_cost_plan_v3_1.md
├── repo_audit_v1.md
├── sdk_runtime_probe.md
├── gesture_definition_v1.md
├── data_collection_protocol.md
├── cost_usage_record.md
├── evaluation_protocol_v1.md
├── model_gap_analysis.md
├── progress_v1.md
└── decisions_v1.md

protocol/
├── gesture_variation_schedule.csv
└── session_orders/

src/
├── acquisition/
├── recording/
├── schemas/
├── preprocessing/
├── segmentation/
├── features/
│   ├── cost_inspired/
│   └── deepskin/
├── datasets/
│   ├── deepskin.py
│   └── cost_adapter.py
├── models/
├── evaluation/
├── runtime/
└── cli/

scripts/
├── probe_sdk.py
├── record_trial.py
├── build_gold_manifest.py
├── inspect_legacy_csv.py
├── inspect_cost_schema.py
├── prepare_cost_7class.py
├── extract_features.py
├── train_grouped_cv.py
├── evaluate_grouped_cv.py
├── train_final_model.py
└── run_streaming_recognizer.py

tests/
├── test_sdk_wrapper.py
├── test_trial_schema.py
├── test_baseline_correction.py
├── test_contact_segmentation.py
├── test_pat_episode_aggregation.py
├── test_cost_feature_extractor.py
├── test_cost_mapping.py
├── test_group_split_no_leakage.py
├── test_training_pipeline.py
├── test_model_serialization.py
└── test_stream_event_contract.py

artifacts/
├── stage_reports/
├── features/
├── cost/
├── evaluation/
└── runtime/
```

---

# 15. 分阶段执行与门控

## 阶段 0：仓库审计

任务：

- 审计 SDK 头文件、示例、DLL、Tool 和 CSV；
- 确认 x64 Python 和 C++ 示例；
- 列出实际 API 签名、缓冲区和返回码；
- 确认现有接口程序边界，但不修改；
- 创建项目结构和决策日志。

产物：

```text
docs/repo_audit_v1.md
docs/progress_v1.md
docs/decisions_v1.md
```

门控：

- 能定位公开矩阵读取 API；
- 能确定 x64 运行依赖；
- 不需要逆向闭源组件。

## 阶段 1：SDK Runtime Probe

任务：

- 初始化和释放设备；
- 读取实际矩阵大小；
- 连续读取 18×29 差分矩阵；
- 同步读取 touch state 和原 SDK JSON；
- 测量帧率、丢帧、时间戳、噪声和设备并发；
- 四角触摸确认方向、转置和镜像。

产物：

```text
docs/sdk_runtime_probe.md
artifacts/stage_reports/stage_1_probe.json
```

门控：

- 可以稳定读取 `[T,18,29]`；
- 行列方向已确认；
- 资源清理和错误处理通过测试。

## 阶段 2：数据 schema 与受控 Recorder

任务：

- 实现 trial recorder；
- 实现 VALID/REDO/UNCERTAIN 确认；
- 生成 variation schedule 和 session order；
- 保存矩阵、时间戳、touch state、SDK JSON 和 metadata；
- 创建 manifest builder。

产物：

```text
docs/data_collection_protocol.md
protocol/gesture_variation_schedule.csv
scripts/record_trial.py
scripts/build_gold_manifest.py
```

门控：

- 可以完整录制、回放和校验单个 trial；
- 原始数据不可覆盖；
- 标签必须经过确认。

## 阶段 3：采集 315 个 Gold 事件

任务：

```text
3 operators × 3 sessions × 7 classes × 5 trials
```

完成后执行：

- 类别计数检查；
- 操作者/session 完整性检查；
- 质量错误检查；
- 重复 trial 和路径冲突检查；
- 采样率和持续时间分布报告。

产物：

```text
data/processed/manifests/gold_manifest.csv
artifacts/stage_reports/gold_data_report.md
artifacts/stage_reports/gold_class_counts.csv
```

门控：

- 正好或至少 315 个 VALID Gold 事件；
- 每名操作者每类至少 15 个；
- 三个独立 session 均存在；
- 严重质量错误样本已重采。

## 阶段 4：CoST 导入、校验与七类源域构建

任务：

- 创建并填写 `docs/cost_usage_record.md`；
- 导入 CoST 官方原始文件；
- 计算 MD5 和 SHA-256；
- 执行 schema、参与者、类别和缺失值检查；
- 映射为七类；
- 执行标签兼容性过滤；
- 生成 source manifest、映射报告、过滤报告和 provenance；
- 不把原始数据提交到 Git。

产物：

```text
docs/cost_usage_record.md
artifacts/cost/cost_provenance.json
artifacts/cost/cost_schema_report.md
artifacts/cost/cost_mapping_report.md
artifacts/cost/cost_class_counts_before_after.csv
artifacts/cost/cost_source_manifest.csv
```

门控：

- 原始文件来源和校验和可追踪；
- 七类映射和过滤规则有版本；
- 每个保留样本具有 source subject、源标签和映射标签；
- 模糊样本没有被强行纳入；
- CoST 文件被 `.gitignore` 正确排除。

## 阶段 5：预处理、切分和特征

任务：

- 实现 baseline correction；
- 实现接触阈值和 micro-contact；
- 实现 PAT episode aggregation；
- 实现 `F0/F1/F2`；
- 对 Gold 数据生成 feature table；
- 为全部特征编写单元测试。

产物：

```text
artifacts/features/feature_dictionary.md
artifacts/features/gold_features.parquet
artifacts/features/feature_coverage_report.csv
```

门控：

- 所有 VALID trial 可提取特征；
- 无 NaN/Inf 未解释残留；
- feature schema 固定；
- 不存在 operator 泄漏字段进入模型。

## 阶段 6：目标域七分类基线

任务：

- 训练 Legacy 对照、RBF-SVM、Extra Trees、Random Forest；
- 比较 F0/F1/F2；
- 执行嵌套 Leave-One-Operator-Out；
- 输出完整三折结果。

产物：

```text
artifacts/evaluation/target_only_results.csv
artifacts/evaluation/target_only_summary.md
artifacts/evaluation/confusion_matrices/
```

门控：

- 分组切分测试通过；
- 每个外层测试操作者从未进入训练和调参；
- 指标可复现；
- 所有实验配置已保存。

## 阶段 7：CoST 源域与迁移实验

必须执行：

- E1 source-only 域偏移诊断；
- E2 类别与域平衡联合训练；
- E3 source score 辅助目标分类；
- E4 CoST 辅助共享特征选择；
- 与相同外层 fold 的 E0 target-only 严格比较；
- 执行多随机种子、每类差异和 pooled out-of-fold bootstrap 分析。

产物：

```text
artifacts/evaluation/cost_source_only_results.csv
artifacts/evaluation/cost_transfer_results.csv
artifacts/evaluation/cost_domain_shift_report.md
artifacts/evaluation/cost_transfer_decision.md
```

门控：

- CoST 训练没有污染 Deepskin 外层测试 fold；
- source weight 和迁移参数只由内层目标域验证选择；
- 所有实验可追踪到映射、过滤和 provenance；
- 只有满足第 11.7 节门控的迁移方案才进入最终模型候选。

## 阶段 8：最终模型选择与训练

任务：

- 根据目标域三折结果选择模型；
- 冻结 preprocessing、feature schema、label map 和阈值；
- 按阶段 7 的最终决策，使用全部 315 个 Gold 事件训练 target-only 模型，或按冻结配方加入 CoST 源数据/源分数训练迁移模型；
- 生成 model card 和 checksums。

产物：

```text
models/deepskin_social_touch_v1/
```

门控：

- model package 可在干净环境加载；
- 预测类别严格限定为七类；
- 训练 manifest 和评估报告可追踪。

## 阶段 9：流式运行时

任务：

- 实现 START/UPDATE/END；
- 增量计算特征；
- provisional 与 final 预测；
- 稳定候选和最终幂等；
- 低置信度事件内部抑制，不输出 UNKNOWN；
- 测量延迟和吞吐量。

产物：

```text
scripts/run_streaming_recognizer.py
artifacts/runtime/runtime_benchmark.md
artifacts/runtime/sample_events.jsonl
```

门控：

- 处理速度高于硬件帧率；
- 不阻塞 SDK 数据读取；
- 最终事件不重复；
- 公共手势值只包含七类。

## 阶段 10：交付与复现

任务：

- 生成安装、采集、训练、评估和运行文档；
- 给出一条命令完成离线评估；
- 给出一条命令启动实时识别；
- 清理临时文件和绝对路径；
- 验证 `.gitignore` 不提交传感器数据和 CoST 数据。

产物：

```text
README.md
docs/runbook_acquisition.md
docs/runbook_training.md
docs/runbook_runtime.md
docs/final_v1_report.md
```

---

# 16. 测试要求

必须至少覆盖：

```text
SDK 初始化失败和清理
矩阵大小和 row-major 转换
空闲基线与负值噪声
非单调时间戳
接触开始/结束防抖
PAT 多脉冲聚合
TAP 单脉冲不被误聚合
CoST label mapping
CoST 文件校验和、provenance 与署名记录
Feature extractor 跨 8×8 和 18×29
归一化坐标
真实时间速度和频率
CoST source subject 与 Deepskin operator 分组字段正确
训练/测试 operator 零重叠
同一 trial 派生数据不跨 fold
联合训练的 domain/class sample weight 正确
Pipeline scaling/imputation 无泄漏
模型序列化前后预测一致
输出类别严格七类
流式 sequence_no 单调
最终事件只发送一次
```

所有随机过程必须支持固定 seed。

---

# 17. Codex 不得自行做出的决定

未经项目负责人明确批准，不得：

- 增加或删除七个核心类别；
- 合并 `TAP` 与 `POKE`；
- 把 `PAT` 改成单次轻拍；
- 把 `Slap` 和 `FistSmash` 作为两个新输出类；
- 增加 UNKNOWN 类别和 UNKNOWN 数据采集；
- 删除、绕过或遗漏 CoST 的来源、署名、许可证、映射和派生模型记录；
- 随机按事件做普通 train/test split；
- 报告基于同一操作者泄漏的数据分数；
- 用旧 SDK 标签自动替代 Gold；
- 直接采用 CoST source-only 模型作为最终模型，或让 CoST 样本未经域权重控制淹没 Deepskin Gold；
- 修改闭源 DLL 或 Tool。

---

# 18. 第一轮交给 Codex 的具体指令

```text
请执行本方案的阶段 0：仓库审计。

要求：
1. 只读检查现有仓库，不修改或逆向任何 DLL/EXE。
2. 找到并记录 x64 SDK 头文件、Python ctypes 示例、C++ 示例、DLL、LIB、HID 依赖和 Tool。
3. 从公开头文件和示例中整理所有 deepskin_* API 的精确签名、参数、缓冲区规则、返回值和调用顺序。
4. 确认 deepskin_get_diff_matrix() 是否可以提供 18×29 原始差分矩阵。
5. 审计现有四份 CSV 的路径、字段、矩阵形状、时间戳和采样率，但不要尝试自动补标签。
6. 检查当前 Python 3.12 x64 与 DLL 位数兼容性。
7. 生成：
   - docs/repo_audit_v1.md
   - docs/progress_v1.md
   - docs/decisions_v1.md
8. 在 docs/repo_audit_v1.md 中列出：
   - 已确认事实；
   - 与本方案不一致的事实；
   - 阶段 1 的可执行入口；
   - 仍依赖硬件或项目负责人的事项。
9. 不开始训练模型，不生成模拟准确率；阶段 0 不下载 CoST，CoST 导入在阶段 4 执行。
10. 完成后运行仓库现有的安全只读检查，并报告实际结果。
```

---

# 19. 参考资料

## CoST 官方数据集

- 4TU.ResearchData：Corpus of Social Touch (CoST)
- DOI：`10.4121/uuid:5ef62345-3b3e-479c-8e1d-c922748c9b29`
- 官方页面：`https://data.4tu.nl/datasets/bc4e5c6a-cfa4-4844-83e4-74a71cae3df6/1`
- 许可证：`CC BY-NC-SA 4.0`

## CoST 传统特征与训练方法

- Jung, M. M., Poel, M., Poppe, R. W., & Heylen, D. K. J.  
  *Automatic recognition of touch gestures in the corpus of social touch.*  
  Journal on Multimodal User Interfaces, 11, 81–96 (2017).  
  DOI：`10.1007/s12193-016-0232-9`

该工作提供了 54 个压力、面积、时间峰值、质心运动、方向、幅度和周期性特征，并采用嵌套 leave-one-subject-out 进行模型选择和独立参与者评估。V3.1 复用其方法思想，并实际引入 CoST 原始数据完成七类源域与迁移实验，但对 Deepskin 的 18×29、约 50 Hz、无物理单位差分矩阵进行重新定义和训练。



# Deepskin V2 轻量时序网络探索协议

- 创建日期：2026-08-24
- 分支：`v2-temporal-exploration`
- V1 基点：`090a49ccf81b2a6429808d94ae27a86c2d898128`（标签 `v1-runtime-freeze`）
- 状态：探索性，不替换 V1 运行模型

## 1. 研究问题

轻量时序模型能否在严格跨操作者评估下超过冻结的 V1 RBF-SVM，并改善依赖完整波形的混淆，重点包括：

- PAT 与 IMPACT；
- TAP 与 POKE；
- STROKE 与 RUB。

## 2. 首个模型

首个候选为小型 Temporal Convolutional Network（TCN），不使用大型 Transformer。

建议输入不是直接展开全部 522 个 taxel，而是逐帧生成紧凑空间表示：

```text
总压力、峰值、接触面积、归一化质心 x/y
+ 4×4 空间池化
= 每帧 21 个通道
```

TCN 初始结构：

```text
Conv1d 21→32，kernel=5，dilation=1
Conv1d 32→32，kernel=5，dilation=2
Conv1d 32→64，kernel=3，dilation=4
masked global mean/max pooling
Linear 128→7
```

使用残差、BatchNorm/LayerNorm、ReLU 和小比例 dropout；模型参数量保持在约 10 万以内。

## 3. 数据与防泄漏约束

- 只使用 315 条已冻结 Deepskin Gold 作为目标域监督数据；首轮不加入 CoST。
- 外层严格 Leave-One-Operator-Out，每折测试 1 名完整操作者。
- 归一化统计、早停、超参数选择只能使用外层训练操作者。
- 同一 trial 的裁剪、补齐或增强序列不得跨训练/验证/测试集合。
- 禁止随机按帧或滑窗混合切分。
- 测试折只评估一次冻结配置，不用于选择 epoch、阈值或结构。

## 4. 序列预处理

- 使用真实 `timestamps_ms`，统一重采样到 50 Hz。
- 先使用 V1 事件分段边界，另保留完整 episode 供 PAT 消融。
- 序列上限初值 256 帧；短序列补零并提供 mask，长序列按事件中心裁剪。
- 空间坐标归一化到 `[0,1]`。
- 每折仅用训练操作者估计通道缩放统计。
- 第一轮不使用空间翻转增强；增强必须作为独立消融。

## 5. 训练 smoke

Smoke 只验证管线，不报告正式性能：

- 固定 seed `20260824`；
- 选一个外层训练折的小子集；
- 运行 2 个 epoch；
- 检查 loss 有限、梯度有限、GPU 实际使用、模型可保存/重载；
- 输出到新的、不可覆盖的 smoke 目录。

Smoke 通过后才允许执行完整实验。

## 6. 正式对照

- 三个固定种子：`20260824, 20260825, 20260826`；
- 主指标：严格外层 pooled Macro F1；
- 次指标：Balanced Accuracy、每类 F1、混淆矩阵、最差操作者折；
- 必须与冻结 V1 的同一 315 条数据和相同外层操作者折比较；
- 报告参数量、训练时间、峰值显存和单事件推理延迟。

进入运行候选至少要求：

1. pooled Macro F1 相对 V1 `0.8535` 提升至少 `0.01`；
2. 三个操作者折中至少两个不低于 V1；
3. PAT/IMPACT 与 TAP/POKE 不出现超过 `0.05` 的核心类别 F1 下降；
4. 多随机种子结论方向一致；
5. 配对 bootstrap 不显示明确负收益；
6. 连续运行延迟和显存满足实时需求。

未通过时保留为负结果，V1 不变。

## 7. TCN v1 结果

冻结的首个 TCN 已完成三折 LOPO：pooled Macro F1 `0.8623`，相对 V1 `0.8535` 提升 `0.0088`。只有 operator_03 折改善；STATIC_TOUCH F1 下降 `0.1064`。三个发布门槛均未通过，因此 TCN v1 不替换 V1。完整结论见 `artifacts/stage_reports/stage_26_temporal_tcn_v1_full_lopo.md`。

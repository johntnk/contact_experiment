# Deepskin 社交触摸 V1 决策日志

## D-001：V1 技术方案

- 日期：2026-08-20
- 状态：已接受
- 决策：采用 `deepskin_social_touch_7class_cost_plan_v3_1.md`，按阶段门控实施。

## D-002：采样率与丢帧表述

- 状态：已冻结
- 决策：报告“主机观测更新率”，不声称公开 SDK 能精确测量硬件丢帧。
- 原因：公开 API 没有硬件时间戳、帧序号或队列深度。

## D-003：第一轮实验范围

- 状态：已冻结
- 决策：第一轮使用 `RBF-SVM × F0/F1`、`Random Forest × F0/F1`，执行 E0 target-only、E1 source-only、E2 joint weighted。
- 后置：Extra Trees、F2 legacy、E3 source-score、E4 source-informed feature selection。

## D-004：315 个 Gold 的定位

- 状态：已冻结
- 决策：315 个事件只作为“三操作者先导数据”，不作产品级人群泛化声明。

## D-005：CoST 过滤

- 状态：暂定
- 决策：保留过滤前/后两个版本、类别数量变化和人工抽查入口；实际阈值在阶段 4 根据源数据 schema 与训练域统计确认。

## D-006：流式输出

- 状态：已冻结
- 决策：V1 不输出 provisional 手势分类。运行中只输出接触状态，episode 结束后输出最终 `GESTURE_END`。
- 原因：完整事件模型直接应用于动作前缀会产生阶段分布偏移。

## D-007：CoST 许可

- 状态：已确认
- 决策：当前用途的 CoST 许可已确认，允许进入源域训练和最终模型候选；仍保留来源、署名、映射、过滤和派生模型记录。

## D-008：CoST 发布门控

- 状态：已冻结
- 决策：若 CoST 迁移未在相同 Deepskin 外层操作者折上产生稳定收益，最终发布 E0 target-only 模型。

## D-009：GPU 使用

- 状态：已记录
- 决策：主机 NVIDIA RTX 5060 Ti 8 GB 可用于后续明确支持 CUDA 的实验。V1 第一轮传统模型和阶段 0 不以 GPU 为依赖。

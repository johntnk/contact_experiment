# 正式运行版本保留清单：hybrid-v1

日期：2026-08-24

## 正式运行入口

- GUI：`scripts/realtime_stream_gui.py`
- GUI SHA-256：`46E4997DF1086E0CEAB5C74E86AF14697C72180F979A9CBCA68A8EC24042991D`
- 模型：`models/deepskin_temporal_tcn_adapted_v1/model.pt`
- 模型 SHA-256：`804EFE1F528CB4DF81051D5188583F7A8C31169CD6DDF540D79A5540D7D063C5`
- 特征：v1，21 通道
- 类别：IMPACT、PAT、POKE、RUB、STATIC_TOUCH、STROKE、TAP

## 正式运行策略

- RUB、STATIC_TOUCH、STROKE：1500 ms 因果滑动窗口，100 ms 更新。
- TAP、POKE、IMPACT、PAT：接触结束并保持释放 300 ms 后，使用完整事件分类。
- 默认置信度阈值：0.50。
- 普通首次确认：3 次；切换确认：2 次。
- 当前版本现场结论：其余类别效果良好；PAT 在动作过程中可能短暂显示 STROKE，但项目负责人验收为“效果不错，不用改”。

## 必须保留

- `models/deepskin_temporal_tcn_adapted_v1/`：正式模型及元数据。
- `scripts/realtime_stream_gui.py`：正式 GUI。
- `src/deepskin_temporal/`、相关运行依赖及测试。
- `data/interim/pat_rub_natural_adaptation_train_20260824_v1/`：当前正式模型的个性化训练依据，共 60 个文件，约 3.40 MB。保留它才能复训和审计。
- `artifacts/evaluation/hybrid_event_path_pat_rub_20260824.json`：正式混合路径的开发回放证据。
- 本文档、`docs/realtime_stream_runtime_v1.md`、`docs/runtime_release_adapted_v1.md`、`experiment_ledger.md` 和 `memory/known_errors.md`。

## 已清理的旧派生产物

以下内容已于 2026-08-24 经项目负责人确认后永久删除，仅保留本节记录：

- 旧候选/实验模型：`deepskin_temporal_tcn_adapted_v1_candidate`、`deepskin_temporal_tcn_adapted_v2_candidate`、`deepskin_temporal_tcn_motion_v2`、`deepskin_temporal_tcn_v1`。
- 旧 TCN 训练输出：`artifacts/temporal/`。
- 除正式混合回放外的旧 TCN/PAT-RUB 回放 JSON。
- `data/interim/pat_rub_live_diagnostic_20260824_v2/`：旧现场诊断数据。
- `scripts/realtime_stream_gui_v1.py`：原纯滑动窗口回退实现。

传统特征模型、CoST 迁移实验、Gold 原始数据和早期七类现场数据属于独立研究资产，不因本次“TCN 旧版本清理”自动删除。

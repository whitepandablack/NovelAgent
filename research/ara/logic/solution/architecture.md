# Solution Architecture

## Evaluation Layers

1. Evalset layer: JSON case 文件定义任务、输入、硬约束、rubric、pass_threshold。当前拆分为 dev、holdout 和兼容入口 basic。
2. Execution layer: StoryQualityEvaluator 用本地 deterministic NovelWorkflow 执行创作动作，保证不依赖外部模型或 API key。
3. Scoring layer: 所有 report total_score 统一为 0-100；原始量纲保存在 raw_scores 或 observed。
4. Evidence layer: research/ara/evidence 保存稳定 evidence ID，claims 只引用 evidence ID，便于 ARA 审查追踪。
5. Future judge layer: 后续接入 LLM judge 时只负责软质量，不替代 hard constraint。

## Current Eval Families

- plan_next_chapter: 验证章节规划硬约束。
- draft_next_chapter_grounding: 验证 beat 是否从抽象提法落到场景动作，raw metric 为 0-5，report 归一化为 0-100。
- revision_non_regression: 验证修订后版本递增、线索状态不回退、不引入未知人物。
- narrative_minimal_pairs: 验证叙事事实判断。
- revision_quality: 验证修订不是追加说明，而是重写为场景。
- character_arc_consistency: holdout，用于检查人物行为是否符合 goal/conflict/arc。
- plot_thread_progression: holdout，用于检查伏笔是否真正推进。
- timeline_causality: holdout，用于检查章节时间线是否记录因果链。

## Development Policy

dev eval 可以用于开发；holdout eval 用于记录边界，不在同一轮里针对性修到全过。只有当新的能力设计完成后，才把相应 holdout case 晋升为 dev 回归。

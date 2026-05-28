# Concepts

## Story Project State

NovelAgent 的被测对象不是单次 prompt 输出，而是一个可持久化项目状态：story bible、人物卡、世界规则、章节大纲、章节草稿、时间线、plot thread、审稿报告和修订任务。

## Creative Operation

一次 eval 应绑定一个具体创作动作，例如 plan_next_chapter、draft_next_chapter、revise_chapter、update_timeline。动作输入为项目状态，输出为新的项目状态或报告。

## Hard Constraint

可确定判断的约束，例如章节号、必需人物、禁止剧透、plot thread 是否仍 open、修订版本是否递增。这些优先由 deterministic evaluator 判断。

## Soft Quality

需要审美或语义判断的质量，例如场景是否有张力、人物是否可信、风格是否稳定。后续可引入 LLM judge 或人工标注，但不能替代 hard constraint。

## Dev Evalset

开发时允许观察和针对性修复的评测集，用于回归测试与快速迭代。

## Holdout Evalset

开发时不针对性调参的评测集，用于暴露过拟合和记录当前能力边界。holdout 初始失败是健康信号，不应被掩盖。

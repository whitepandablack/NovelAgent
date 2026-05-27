# 文献初筛：故事质量与长篇 agent 评测

## NoCha / One Thousand and One Pairs

- 来源：https://arxiv.org/abs/2406.16264
- 相关性：高。
- 关键启发：用近期小说构造 true/false minimal claim pairs，要求模型判断哪个声明符合整本书事实。该方法比 needle-in-a-haystack 更接近长篇叙事理解，因为大量样本需要全书级推理。
- 可迁移点：为 NovelAgent 的项目状态生成“真/假叙事声明对”，测试人物、世界规则、伏笔和时间线一致性。

## LongGenBench

- 来源：https://arxiv.org/abs/2410.04199
- 相关性：中高。
- 关键启发：长上下文评测不应只测检索，还应测长文本生成是否保持上下文准确性和连贯性。
- 可迁移点：NovelAgent 的 eval 应包含长篇生成退化测试，例如第 8 章是否仍遵守第 1 章世界规则。

## LongGenBench: Benchmarking Long-Form Generation in Long Context LLMs

- 来源：https://arxiv.org/abs/2409.02076
- 相关性：中高。
- 关键启发：复杂指令约束下的长文本生成需要独立 benchmark。
- 可迁移点：章节任务可以包含多个约束：必须推进某伏笔、禁止揭示真相、改变人物关系、保持风格。

## STORYEVAL

- 来源：https://m.aaai.org/Library/Symposia/Spring/2009/ss09-06-017.php
- 相关性：高。
- 关键启发：叙事生成早已有面向故事结构的经验评测框架。
- 可迁移点：把传统 narrative generation 的可理解性、连贯性、趣味性等维度转译成 NovelAgent 的结构化 rubric。

## STORIUM

- 来源：https://arxiv.org/abs/2010.01717
- 相关性：高。
- 关键启发：面向 machine-in-the-loop story generation，包含长故事、角色目标、属性等细粒度自然语言标注。
- 可迁移点：NovelAgent 的项目状态可以借鉴 STORIUM 的角色目标和属性标注方式，把人物弧线、目标变化、关系状态纳入 eval case。

## G-Eval

- 来源：https://arxiv.org/abs/2303.16634
- 相关性：高。
- 关键启发：LLM-as-judge 使用 CoT 和 form-filling rubric 可提升与人类评价的一致性，但存在偏向 LLM 生成文本的风险。
- 可迁移点：NovelAgent 可以用固定 rubric judge 评估风格、场景化、人物可信度，但不能只依赖 judge；必须与规则评测分层。

## AgentBench

- 来源：https://arxiv.org/abs/2308.03688
- 相关性：中。
- 关键启发：agent 应在交互环境中评测长期推理、决策和指令遵循，而不是只测单轮输出。
- 可迁移点：NovelAgent eval 应评测多步流程：规划、起草、审稿、修订、导出。

## SWE-bench

- 来源：https://arxiv.org/abs/2310.06770
- 相关性：中高。
- 关键启发：固定真实任务、上下文和可执行验证标准，使 agent 能力可比较。
- 可迁移点：故事 eval 可以采用“项目状态 + 创作任务 + expected state delta + 自动检查”的形式。

# Claims

## C1：故事质量 eval 应以状态变化为中心

Statement：长篇小说 agent 的核心评测单元应是“给定项目状态，执行创作动作，验证状态变化”，而不是单独评价输出文本。

Evidence basis：SWE-bench 的任务形式和 AgentBench 的交互环境评测说明，agent 能力需要在固定上下文与任务中验证。

Status：hypothesis。

## C2：minimal-pair 可以转化为叙事记忆评测

Statement：NoCha 的 true/false claim pair 方法可迁移到 NovelAgent，用于测试 agent 是否维护人物、世界规则、伏笔和时间线事实。

Evidence basis：NoCha 针对近期小说构造 minimally different true/false claims，并强调全书级 reasoning。

Status：hypothesis。

## C3：规则评测和 LLM judge 必须分层

Statement：NovelAgent 不应只依赖 LLM-as-judge；规则评测负责硬约束，LLM judge 负责风格、场景化和人物可信度等软质量。

Evidence basis：G-Eval 支持 rubric judge 的有效性，但也提示 LLM evaluator 可能偏向 LLM 生成文本。

Status：hypothesis。


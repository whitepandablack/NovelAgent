# Related Work

## Narrative Claim Verification

NoCha 使用小说中的 minimally different true/false claims 测试长上下文叙事理解。NovelAgent 借鉴其“相似表述、真假差异小”的设计，但把对象从已出版小说阅读理解迁移到生成项目状态审计。

Evidence: EV-NOCHA-001.

## LLM-as-Judge

G-Eval 说明 rubric 化 LLM judge 可以提升与人类评价的一致性。NovelAgent 后续会把它用于软质量层，但当前阶段先保留 deterministic workflow，避免评测本身绑定单一模型供应商。

Evidence: EV-GEVAL-001.

## Task-Grounded Agent Benchmarks

SWE-bench 与 AgentBench 的共同启发是：agent 能力应在任务环境和状态转移中测量，而不是只看一次自然语言回答。NovelAgent 因此采用 StoryEvalCase schema，将 request、required、forbidden、rubric 和 pass_threshold 固定为可复现输入。

Evidence: EV-SWEBENCH-001, EV-AGENTBENCH-001.

## Story Generation Evaluation

STORIUM 强调故事生成有开放输出空间，需要丰富上下文、人物属性和真实作者编辑信号辅助评价。NovelAgent 的当前版本先实现结构化上下文和可审计规则，后续再引入人工/LLM preference 层。

Evidence: EV-STORIUM-001.

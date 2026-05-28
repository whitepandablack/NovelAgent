# Claims

## C1: 故事质量 eval 应以状态变化为中心

Statement: 长篇小说 agent 的核心评测单元应是“给定项目状态，执行创作动作，验证状态变化”，而不是只评价单段输出文本。

Evidence: EV-SWEBENCH-001, EV-AGENTBENCH-001.

Status: hypothesis.

## C2: minimal-pair 可以转化为叙事记忆评测

Statement: NoCha 的 true/false claim pair 方法可以迁移到 NovelAgent，用于测试 agent 是否维护人物、世界规则、伏笔和时间线事实。

Evidence: EV-NOCHA-001.

Status: active design principle.

## C3: 规则评测和 LLM judge 必须分层

Statement: NovelAgent 不应只依赖 LLM-as-judge；规则评测负责硬约束，LLM judge 或人工偏好评测负责风格、场景化和人物可信度等软质量。

Evidence: EV-GEVAL-001, EV-STORIUM-001.

Status: active design principle.

## C4: evalset 必须拆分 dev 与 holdout

Statement: 同一批 case 既用于调参又用于宣称能力会导致自刷分风险；开发集和保留集必须分开记录。

Evidence: EV-SWEBENCH-001, EV-AGENTBENCH-001.

Status: active design principle.

## C5: 长篇能力需要测因果、人物弧线和线索推进

Statement: 关键词覆盖不足以代表会写小说；长篇故事 agent 至少要测人物行为是否符合 goal/conflict/arc、伏笔是否推进、章节之间是否存在因果链。

Evidence: EV-NOCHA-001, EV-STORIUM-001.

Status: active design principle.

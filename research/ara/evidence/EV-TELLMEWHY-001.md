# EV-TELLMEWHY-001: TellMeWhy 启发

- Source: TellMeWhy, Stony Brook NLP, https://stonybrooknlp.github.io/tellmewhy/
- Evidence type: dataset/task design.
- Stable takeaway: TellMeWhy 聚焦叙事中“为什么”问题，要求解释人物行动或事件发生背后的原因。
- NovelAgent applicability: 适合借鉴为人物动机和事件原因评测，要求 Agent 在章节计划和正文里保留可审计动机链。
- Mapped capability: 人物选择链、隐含因果、时间线因果链。
- Limitation: 主要是问答式理解任务，不直接覆盖写作 agent 的状态变更和修订流程。
- Derived case template: `research_tellmewhy_glucose_style_motivation_cause` in `evaluation/evalsets/story_agent_research_dev.json`.

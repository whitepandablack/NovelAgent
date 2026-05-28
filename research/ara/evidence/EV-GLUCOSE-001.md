# EV-GLUCOSE-001: GLUCOSE 启发

- Source: GLUCOSE: Generalized and Contextualized Story Explanations, arXiv:2009.07758, https://arxiv.org/abs/2009.07758
- Evidence type: dataset/task design.
- Stable takeaway: GLUCOSE 将故事事件转化为上下文化常识解释，覆盖事件前因、后果、人物状态和隐含因果。
- NovelAgent applicability: 适合借鉴为 timeline causality 检查，要求章节之间保留“因为 X，所以 Y”的可审计链条。
- Mapped capability: 时间线因果链、人物动机、隐含后果。
- Limitation: 偏短文本常识解释，不直接评小说审美、章节结构或伏笔兑现。
- Derived case template: `research_tellmewhy_glucose_style_motivation_cause` in `evaluation/evalsets/story_agent_research_dev.json`.

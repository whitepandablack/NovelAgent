# EV-ROCSTORIES-001: ROCStories / Story Cloze 启发

- Source: ROCStories Corpus / Story Cloze Test, University of Rochester NLP, https://cs.rochester.edu/nlp/rocstories/
- Evidence type: dataset/task design.
- Stable takeaway: ROCStories 用短事件序列和合理结尾判断来评估故事常识、时间推进和因果合理性。
- NovelAgent applicability: 适合借鉴为“给前四步剧情，让 Agent 生成或判断合理下一步”的 eval case。
- Mapped capability: 时间线因果链、合理下一步、章节计划自然推进。
- Limitation: 原任务是短故事，不覆盖长篇伏笔、项目状态持久化和多章修订。
- Derived case template: `research_rocstories_style_causal_next_step` in `evaluation/evalsets/story_agent_research_dev.json`.

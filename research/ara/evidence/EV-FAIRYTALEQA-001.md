# EV-FAIRYTALEQA-001: FairytaleQA 启发

- Source: FairytaleQA dataset, https://huggingface.co/datasets/GEM/FairytaleQA
- Evidence type: dataset/task design.
- Stable takeaway: FairytaleQA 围绕叙事元素提出问答任务，包括人物、行动、感受、结果等。
- NovelAgent applicability: 适合借鉴为人物行动与正文兑现度检查，让评测不只看关键词，而是问“谁做了什么、为什么、结果如何”。
- Mapped capability: 人物选择链、正文兑现度。
- Limitation: 数据域偏童话阅读理解，不直接评长篇小说生成、伏笔状态或修订。
- Derived case template: `research_fairytaleqa_style_character_action` in `evaluation/evalsets/story_agent_research_dev.json`.

# NovelAgent Story Quality Eval 研究日志

## 2026-05-27：启动研究

目标是把 NovelAgent 的“会写故事”变成可测量、可比较、可迭代的能力，而不是只靠主观感觉判断。

已安装 ARA 三件套：

- `ara-compiler`
- `ara-research-manager`
- `ara-rigor-reviewer`

第一轮外部文献扫描锁定六个方向：

1. NoCha：用近期小说构造 true/false minimal claim pairs，评测长上下文模型是否能跨整本书推理。
2. LongGenBench：评测长上下文生成，而不仅是 needle retrieval。
3. STORYEVAL：早期 narrative generation 经验评测框架。
4. G-Eval：LLM-as-judge + rubric/form-filling 的 NLG 评测方案。
5. AgentBench：把 LLM 作为 agent 放入交互环境评测。
6. SWE-bench：用真实任务、可执行测试和固定实例评估 agent 能力。

初步判断：NovelAgent 的 eval 体系应该融合 NoCha 的 minimal-pair、SWE-bench 的 executable/regression mindset、G-Eval 的 rubric judge，以及 narrative generation 的故事维度。

## 2026-05-28：第一版可执行 eval 落地

新增 `evaluation/` 工作区和 `StoryQualityEvaluator`，第一版先不接 LLM judge，只实现可复现的规则型评测。

已落地 case：

1. `star_clinic_plan_chapter_02`：验证下一章计划是否满足章节号、人物、beat 和禁用泄露约束。
2. `star_clinic_beat_grounding`：验证当前模板生成是否只是提到 beat，而没有通过具体场景行动兑现 beat。
3. `star_clinic_revision_non_regression`：验证修订能递增版本，并保持核心剧情线索开放。

首轮结果：2/3 通过。失败项是 `beat_grounding`，这符合预期，说明当前 deterministic drafter 仍是解释式模板，不具备真正的场景化叙事能力。

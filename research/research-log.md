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

## 2026-05-28：第二版 eval 扩展 minimal-pair 和修订质量

新增两个 case：

1. `star_clinic_minimal_pairs`：借鉴 NoCha 的 true/false pair，检查当前结构化项目状态能否支持叙事事实判断。
2. `star_clinic_revision_quality`：把修订质量从 non-regression 中拆出，专门惩罚“追加审稿说明而非重写小说场景”的修订。

第二轮结果：3/5 通过。新增的 `minimal_pairs` 通过，说明结构化状态已经足以支撑最小叙事事实判断；`revision_quality` 失败，确认当前修订流程只是工程闭环，还不是可接受的小说重写。

## 2026-05-28：用 eval 反向改进写作 workflow

根据第二轮 eval 的两个失败项，改进 `draft_next_chapter` 和 `revise_chapter`：

- 起草不再输出“本章需要完成的节拍包括”式任务说明，而是把 beat 写进走廊、扫描记录、病历背面和人物对话等场景动作。
- 修订不再追加“修订补充”，而是根据章节计划重写场景，并在文本中保留“重排场景”的修订意图。
- 下一章计划稳定保留主角林澈，同时加入章节关键人物米拉，避免场景中人物自我重复。

第三轮结果：5/5 通过。`beat_grounding` 从 1 提升到 5，`revision_quality` 从 20 提升到 80。

## 2026-05-28：ARA 预审查

对当前 `research/ara` 做了 pre-Level-2 审查，结论是：当前 ARA 已经有问题、claims、实验草案和探索树，但还不能进入正式 ARA Seal Level 2。

主要问题：

- 缺少 source-specific evidence 文件。
- 当前 eval 只覆盖 `星诊所` 一个项目，存在过拟合风险。
- `beat_grounding` 使用 0-5 分，而其他分数多为 0-100，报告量纲不统一。
- `revision_quality` 仍是启发式规则，不能代表真实修订质量。
- minimal-pair 太接近关键词匹配，叙事记忆压力不足。

下一步应先补完整 ARA 结构和第二波更难 eval，再正式运行 Level 2 语义审查。
# 2026-05-28: Eval trustworthiness phase

- Split Star Clinic evals into dev and holdout sets.
- Normalized report scores to 0-100 while preserving raw beat grounding score.
- Added holdout probes for character arc, plot thread progression, timeline causality, and harder minimal pairs.
- Added ARA evidence entries for NoCha, G-Eval, SWE-bench, AgentBench, and STORIUM.
- Reworked ARA claims to cite stable evidence IDs.

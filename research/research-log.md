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


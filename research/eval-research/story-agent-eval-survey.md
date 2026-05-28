# NovelAgent 小说 Agent 评测调研综述

## 结论

NovelAgent 的评测对象不是通用大模型，而是“能否把长篇小说项目状态转化为可信章节”的 Agent。因此评测需要三层：

1. 规则层：检查 `narrative_contract` 是否包含人物选择链、伏笔推进链、时间线因果链。
2. 状态层：检查 plot thread、timeline、revision task 是否真的发生结构变化。
3. Judge 层：用 Qwen Judge 评软质量，但必须引用正文或结构证据；没有 evidence 不得高分。

## 数据集矩阵

| 数据集 | 结论 | 可借鉴题型 | 映射到 NovelAgent 能力 | 限制 |
| --- | --- | --- | --- | --- |
| NoCha | 只能借鉴 | 长篇小说事实判断、true/false 近似陈述 | 正文兑现度、时间线因果链 | 目标是阅读理解，不直接评生成质量 |
| STORIUM | 只能借鉴 | 角色目标、故事卡、作者编辑反馈、长故事续写 | 人物选择链、伏笔推进链、修订有效性 | 原始任务依赖交互式多人写作语境 |
| ROCStories | 只能借鉴 | 给前四步剧情，判断/生成合理结尾 | 时间线因果链、合理下一步 | 短故事，不覆盖长篇伏笔和多章状态 |
| FairytaleQA | 只能借鉴 | 围绕人物、行动、感受、结果的问答 | 人物选择链、正文兑现度 | 偏阅读理解，童话风格与目标小说域不同 |
| TellMeWhy | 只能借鉴 | “为什么”问题，解释人物动机和事件原因 | 人物动机、隐含因果 | 不直接评章节规划和修订 |
| GLUCOSE | 只能借鉴 | 事件前因后果和常识解释 | 时间线因果链、隐含因果 | 偏短文本常识，不直接覆盖小说审美 |
| 通用 LLM eval harness | 不适合 | MMLU、通用问答、困惑度等 | 仅可做模型底座参考 | 评模型通用能力，不评 NovelAgent 的写作状态机 |

## 可直接用 / 只能借鉴 / 不适合

可直接用：当前没有一个外部数据集可以原封不动替代 NovelAgent 评测。原因是 NovelAgent 的核心能力依赖项目状态、章节计划、正文、修订任务和长期伏笔状态的联动。

只能借鉴：NoCha、STORIUM、ROCStories、FairytaleQA、TellMeWhy、GLUCOSE。它们提供题型和标注思想，但需要改写成 NovelAgent 本地 case。

不适合：只评通用模型能力的 benchmark，例如通用 lm-evaluation-harness 任务。它可以作为模型底座参考，但不能说明 Agent 会不会写好小说。

## NovelAgent 能力映射

| NovelAgent 能力 | 结构化证据 | Judge 关注点 | 外部启发 |
| --- | --- | --- | --- |
| 人物选择链 | `character_choice_chain` | 选择是否主动、动机是否可信、代价是否明确 | FairytaleQA、TellMeWhy、STORIUM |
| 伏笔推进链 | `plot_thread_progression` 与 plot thread 状态变化 | 线索是否推进而非重复提到 | STORIUM、NoCha |
| 时间线因果链 | `timeline_causality` 与 timeline 事件摘要 | 因果是否自然、前后是否可追溯 | ROCStories、GLUCOSE、TellMeWhy |
| 正文兑现度 | 正文内容、章节计划、contract 对齐 | 正文是否把结构写成场景，而不是说明书 | NoCha、FairytaleQA |
| 修订有效性 | revision task 完成、revision 递增、正文重写 | 修订是否改善问题且不破坏已建立事实 | STORIUM、G-Eval |

## 评测设计原则

- 规则层和状态层是硬门槛：结构字段缺失、状态未变化时不能靠 Judge 主观高分通过。
- Judge 只评软质量：人物可信度、因果自然度、伏笔推进效果、正文兑现度。
- Judge 输出必须结构化：`dimension`、`score`、`evidence`、`failure_reason`、`revision_advice`。
- 每个外部启发 case 必须本地可跑，不依赖下载完整私有数据集。
- dev evalset 可用于开发迭代，holdout 只用于暴露能力边界。

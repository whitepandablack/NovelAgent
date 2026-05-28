# NovelAgent

NovelAgent 是一个长篇中文小说创作 Agent 框架。当前项目同时保留两层能力：

- `NovelWorkflow`：本地确定性 baseline，方便无密钥测试和状态回归。
- `LLMNovelWorkflow`：大模型写作核心，让 LLM 参与章节规划、正文起草、审稿和修订。

## 核心能力

- 创建小说项目并保存结构化 JSON 状态。
- 维护故事圣经、人物卡、卷纲、章节纲、世界规则、剧情线和时间线。
- 使用 LLM 生成章节计划、人物选择链、伏笔推进链、时间线因果链和正文草稿。
- 使用 LLM 审稿并生成修订任务。
- 使用 LLM 根据审稿任务重写章节。
- 导出 Markdown 正文。
- 运行故事质量 eval，检查结构化状态和能力边界。

## 本地 baseline

```powershell
$env:PYTHONPATH='src'
python -m novelagent seed --root sample_projects --title 星诊所 --premise 一名神经科医生发现震颤中藏着记忆。 --genre 医疗科幻 --style 安静悬疑
```

```powershell
$project='sample_projects/novel/novel_project.json'

python -m novelagent status --project $project
python -m novelagent plan-next --project $project
python -m novelagent draft-next --project $project
python -m novelagent review --project $project --chapter 2
python -m novelagent revise --project $project --chapter 2
python -m novelagent export --project $project --out manuscript.md
```

## LLM 写作核心

LLM 配置只从环境变量读取，不把 API Key 写入源码或文档：

- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL`
- `DASHSCOPE_MODEL`
- `DASHSCOPE_ENABLE_THINKING`

让大模型真正参与规划、起草、审稿和修订：

```powershell
$env:DASHSCOPE_API_KEY='你的密钥'
$env:PYTHONPATH='src'
$project='sample_projects/novel/novel_project.json'

python -m novelagent plan-next --project $project --llm
python -m novelagent draft-next --project $project --llm
python -m novelagent review --project $project --chapter 2 --llm
python -m novelagent revise --project $project --chapter 2 --llm
```

LLM workflow 会要求模型输出中文 JSON，并包含：

- 人物选择链：目标、压力、决定、代价、后果。
- 伏笔推进链：线索原状态、新状态、证据、新问题。
- 时间线因果链：前因、后果、因为/所以关系。

这些结构会保存到章节计划和章节草稿的 `narrative_contract` 字段中，供后续 eval 检查。

## 测试

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

## 故事质量 Eval

```powershell
$env:PYTHONPATH='src;.'
python -m evaluation.run_eval --evalset evaluation/evalsets/star_clinic_dev.json --out-dir evaluation/results/dev
python -m evaluation.run_eval --evalset evaluation/evalsets/star_clinic_holdout.json --out-dir evaluation/results/holdout
```

`dev` 用于开发回归，`holdout` 用于记录当前能力边界。holdout 失败不等于测试框架坏了，而是说明 agent 在人物弧线、伏笔推进、因果链或深层叙事判断上仍有待增强。

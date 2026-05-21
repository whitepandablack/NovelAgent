# NovelAgent

NovelAgent 是一个本地优先的长篇中文小说创作 Agent 框架。当前版本重点建设可测试、可审计的创作工作流：先用确定性 workflow 管理项目状态、章节计划、草稿、审稿和修订，再为后续 LLM provider 与更高层 agent 调度预留接口。

## 核心能力

- 创建小说项目并保存结构化 JSON 状态。
- 维护故事圣经、人物卡、卷纲、章纲、世界规则、剧情线索和时间线。
- 规划下一章并避免重复规划。
- 根据章节计划起草下一章。
- 审稿未知人物、重复章节和章纲节拍缺失。
- 将审稿问题转换为修订任务，并生成修订版章节。
- 导出 Markdown 正文。

## 本地运行

```powershell
$env:PYTHONPATH='src'
python -m novelagent seed --root sample_projects --title 星诊所 --premise 一名神经科医生发现震颤中藏着记忆。 --genre 医疗科幻 --style 安静悬疑
```

## 作家工作台 CLI

```powershell
$project='sample_projects/novel/novel_project.json'

python -m novelagent status --project $project
python -m novelagent plan-next --project $project
python -m novelagent draft-next --project $project
python -m novelagent review --project $project --chapter 2
python -m novelagent revise --project $project --chapter 2
python -m novelagent export --project $project --out manuscript.md
```

## 配置

LLM 配置只从环境变量读取，不把 API Key 写入源码或文档：

- `DASHSCOPE_API_KEY`
- `DASHSCOPE_BASE_URL`
- `DASHSCOPE_MODEL`
- `DASHSCOPE_ENABLE_THINKING`

当前 workflow 不依赖真实 LLM 调用，因此可以在没有密钥的环境中完整运行测试。

## 测试

```powershell
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
```

# NovelAgent 设计文档

## 目标

构建一个本地优先的长篇中文小说创作 Agent 框架。框架需要保存结构化故事记忆，分阶段生成创作产物，并在文本进入项目状态前执行连续性审稿。

## MVP 范围

第一版实现一个完整闭环：

1. 接收书名、核心设定、题材和风格。
2. 创建带结构化 JSON 状态的项目目录。
3. 生成故事圣经、人物卡、三卷大纲、前三章章纲和第一章草稿。
4. 对生成章节执行连续性审稿。
5. 持久化所有产物，方便后续 Agent 修改或续写。

## 架构

MVP 使用普通 Python 模块和标准库持久化。这样可以让核心行为不绑定任何单一模型供应商。后续版本可以围绕同一套领域服务添加 LangGraph 节点。

主要单元：

- `NovelProject`：负责持久化小说项目状态。
- `StoryBible`、`CharacterCard`、`OutlineItem`、`ChapterDraft` 和 `ReviewReport`：在不同 Agent 间共享的结构化创作产物。
- `NovelWorkflow`：编排种子项目创作闭环。
- `ContinuityChecker`：根据已知人物和项目记忆校验章节草稿。

## MVP 暂不包含

- 实时 LLM 调用。
- 向量记忆。
- LangGraph 运行时编排。
- Web UI。
- 多书系列管理。


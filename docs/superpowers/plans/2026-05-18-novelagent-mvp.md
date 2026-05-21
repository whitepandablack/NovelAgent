# NovelAgent MVP 实施计划

> **给 Agent 工作者：** 必须使用子技能 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans`，按任务逐项实现本计划。步骤使用复选框（`- [ ]`）语法跟踪。

**目标：** 构建一个可测试、本地优先的长篇小说创作 Agent 框架 MVP。

**架构：** 实现聚焦的 Python 模块，分别负责项目状态持久化、结构化故事产物、确定性种子生成和连续性审稿。第一轮闭环暂不接入模型供应商和 LangGraph。

**技术栈：** Python 3 标准库、`unittest`、JSON 持久化。

---

### 任务 1：项目状态与持久化

**文件：**
- 创建：`src/novelagent/models.py`
- 创建：`src/novelagent/project.py`
- 创建：`src/novelagent/__init__.py`
- 测试：`tests/test_project.py`

- [ ] 编写失败测试，证明项目能够保存并读取书名、核心设定、人物卡和章节草稿。
- [ ] 运行 `python -m unittest tests.test_project -v`，确认当前因导入或行为缺失而失败。
- [ ] 实现数据类和 JSON 持久化。
- [ ] 重新运行测试，确认测试通过。

### 任务 2：连续性审稿

**文件：**
- 创建：`src/novelagent/review.py`
- 测试：`tests/test_review.py`

- [ ] 编写失败测试：章节引用未知人物时应产生审稿问题。
- [ ] 运行 `python -m unittest tests.test_review -v`，确认测试失败。
- [ ] 实现 `ContinuityChecker.review_chapter`。
- [ ] 重新运行测试，确认测试通过。

### 任务 3：种子小说工作流

**文件：**
- 创建：`src/novelagent/workflow.py`
- 测试：`tests/test_workflow.py`

- [ ] 为完整种子工作流编写失败测试。
- [ ] 运行 `python -m unittest tests.test_workflow -v`，确认测试失败。
- [ ] 实现确定性的故事圣经、人物、大纲、第一章和审稿报告生成。
- [ ] 重新运行测试，确认测试通过。


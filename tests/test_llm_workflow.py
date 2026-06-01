import tempfile
import unittest
from pathlib import Path

from novelagent import LLMNovelWorkflow, NovelRequest, NovelWorkflow


class FakeLLMClient:
    def __init__(self):
        self.calls = []

    def generate_json(self, *, system_prompt, user_payload):
        self.calls.append({"system_prompt": system_prompt, "user_payload": user_payload})
        task = user_payload["task"]
        if task == "seed_project":
            return {
                "story_bible": {
                    "logline": "走马灯星球上的文明从结局向起点返退。",
                    "themes": ["倒叙危险", "文明返退", "接受感情"],
                    "rules": ["故事必须倒着展开", "远距离光接触之后文明开始退变"],
                    "style_notes": ["克制", "危险感强"],
                },
                "characters": [
                    {
                        "name": "未启者",
                        "role": "主角",
                        "description": "模型可能多给的字段",
                        "goal": "活过倒退文明的最危险开端",
                        "conflict": "不敢开启自己的人生",
                        "arc": "从不敢开启人生到主动接受别人的感情",
                    }
                ],
                "volume_outline": [
                    {
                        "title": "第一卷：倒着开始的危险",
                        "summary": "故事从文明退变后的危险现场开始。",
                        "beats": ["最危险的开场"],
                    }
                ],
                "chapter_outlines": [
                    {
                        "title": "第一章：倒亮的星",
                        "summary": "主角在文明返退现场第一次被迫选择。",
                        "beats": ["倒序开场", "光接触遗迹", "拒绝逃避"],
                    }
                ],
                "world_rules": [
                    {
                        "code": "WR-001",
                        "description": "文明像走马灯一样整体返退。",
                        "source": "用户设定",
                    }
                ],
                "plot_threads": [
                    {
                        "code": "PT-001",
                        "title": "走马灯文明返退",
                        "status": "open",
                        "related_chapters": [1],
                        "payoff": "解释光接触之后为何退变。",
                    }
                ],
                "first_chapter": {
                    "number": 1,
                    "title": "倒亮的星",
                    "summary": "主角从最危险的一刻开始面对返退。",
                    "scenes": ["坠落的光城"],
                    "content": "星球像地球一样熟悉，却在倒着燃烧。未启者第一次没有逃走。",
                    "referenced_characters": ["未启者"],
                    "narrative_contract": {
                        "character_choice_chain": [
                            {"character": "未启者", "choice": "留下"}
                        ],
                        "plot_thread_progression": [
                            {"thread_code": "PT-001", "current_state": "危险开场"}
                        ],
                        "timeline_causality": [
                            {"cause": "文明开始返退", "effect": "主角不能再旁观"}
                        ],
                    },
                },
            }
        if task == "plan_next_chapter":
            return {
                "number": 2,
                "title": "第二章：米拉的警告",
                "goal": "林澈在米拉的警告下决定暂缓上报记录。",
                "scenes": ["走廊交接扫描记录", "林澈选择继续追查"],
                "beats": ["第二位见证者", "矛盾记忆", "规则浮现"],
                "required_characters": ["林澈", "米拉"],
                "plot_threads": ["PT-001"],
                "narrative_contract": {
                    "character_choice_chain": [
                        {
                            "character": "林澈",
                            "goal": "确认震颤记录的来源",
                            "pressure": "上报会让米拉暴露",
                            "decision": "暂缓上报，先追查记录背后的规则",
                            "cost": "承担违规调查风险",
                            "consequence": "他从旁观者转向主动承担",
                        }
                    ],
                    "plot_thread_progression": [
                        {
                            "thread_code": "PT-001",
                            "previous_status": "open",
                            "new_status": "developed",
                            "evidence": "第二份扫描记录与第一章异常互相印证",
                            "new_question": "震颤为什么只带回短期记忆",
                        }
                    ],
                    "timeline_causality": [
                        {
                            "cause_chapter": 1,
                            "effect_chapter": 2,
                            "cause": "第一章出现无法解释的震颤记录",
                            "effect": "米拉带来警告并迫使林澈选择",
                            "because": "异常记录证明官方解释不完整",
                        }
                    ],
                },
            }
        if task == "draft_chapter":
            return {
                "summary": "林澈决定承担违规追查的代价。",
                "content": "米拉把扫描记录递给林澈。因为第一章的异常无法被官方解释，他暂缓上报，选择追查规则。",
                "referenced_characters": ["林澈", "米拉"],
                "narrative_contract": user_payload["plan"]["narrative_contract"],
            }
        if task == "review_chapter":
            return {
                "passed": False,
                "summary": "需要补强代价。",
                "issues": [
                    {
                        "category": "character_cost",
                        "message": "林澈的违规代价还不够具体。",
                        "severity": "warning",
                    }
                ],
            }
        if task == "revise_chapter":
            return {
                "summary": "林澈承担被停职调查的风险。",
                "content": "米拉把扫描记录递给林澈。因为第一章的异常无法被官方解释，他暂缓上报，并接受可能被停职调查的代价。",
                "referenced_characters": ["林澈", "米拉"],
                "narrative_contract": user_payload["chapter"]["narrative_contract"],
            }
        raise AssertionError(f"Unexpected task: {task}")


class LLMNovelWorkflowTests(unittest.TestCase):
    def test_llm_seed_project_uses_model_outputs_for_first_chapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            llm = FakeLLMClient()
            project = LLMNovelWorkflow(llm).run_seed_project(
                NovelRequest(
                    title="走马灯星球",
                    premise="星球和地球无限相似，文明整体返退。",
                    genre="文明退变悬疑",
                    style="倒叙，非常危险",
                ),
                Path(tmp),
            )

            self.assertEqual(llm.calls[0]["user_payload"]["task"], "seed_project")
            self.assertEqual(project.chapters[0].title, "倒亮的星")
            self.assertIn("走马灯星球", project.story_bible.logline)
            self.assertIn("character_choice_chain", project.chapters[0].narrative_contract)
            self.assertNotIn("林澈", project.chapters[0].content)

    def test_llm_workflow_uses_model_outputs_for_plan_draft_review_and_revision(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = NovelWorkflow()
            project = base.run_seed_project(
                NovelRequest(
                    title="星诊所",
                    premise="一名神经科医生发现震颤中藏着记忆。",
                    genre="医疗科幻",
                    style="安静悬疑",
                ),
                Path(tmp),
            )
            llm = FakeLLMClient()
            workflow = LLMNovelWorkflow(llm)

            plan = workflow.plan_next_chapter(project)
            chapter = workflow.draft_next_chapter(project)
            review = workflow.review_chapter(project, chapter.number)
            workflow.create_revision_tasks(project, review)
            revised = workflow.revise_chapter(project, chapter.number)

            self.assertEqual([call["user_payload"]["task"] for call in llm.calls], [
                "plan_next_chapter",
                "draft_chapter",
                "review_chapter",
                "revise_chapter",
            ])
            self.assertEqual(plan.title, "第二章：米拉的警告")
            self.assertIn("character_choice_chain", plan.narrative_contract)
            self.assertIn("plot_thread_progression", chapter.narrative_contract)
            self.assertIn("因为第一章", chapter.content)
            self.assertFalse(review.passed)
            self.assertEqual(revised.revision, 1)
            self.assertIn("停职调查", revised.content)


class MalformedContractLLMClient:
    def generate_json(self, *, system_prompt, user_payload):
        return {
            "number": 2,
            "title": "第二章",
            "goal": "推进线索",
            "scenes": ["走廊"],
            "beats": ["证据"],
            "required_characters": ["林澈"],
            "plot_threads": ["PT-001"],
            "narrative_contract": {
                "plot_thread_progression": ["PT-001 developed"],
                "timeline_causality": ["因为异常所以追查"],
            },
        }


class LooseProgressionLLMClient:
    def generate_json(self, *, system_prompt, user_payload):
        return {
            "number": 2,
            "title": "第二章",
            "goal": "推进线索",
            "scenes": ["走廊"],
            "beats": ["证据"],
            "required_characters": ["林澈"],
            "plot_threads": ["PT-001"],
            "narrative_contract": {
                "plot_thread_progression": [
                    {
                        "thread_code": "PT-001",
                        "previous_state": "发现异常",
                        "current_state": "确认系统会掩盖异常",
                    }
                ],
            },
        }


class MalformedSeedMetadataLLMClient(FakeLLMClient):
    def generate_json(self, *, system_prompt, user_payload):
        result = super().generate_json(system_prompt=system_prompt, user_payload=user_payload)
        if user_payload["task"] == "seed_project":
            result["characters"].insert(0, "not a character object")
            result["volume_outline"].insert(0, "not an outline object")
            result["chapter_outlines"].insert(0, "not a chapter outline object")
            result["world_rules"].insert(0, "not a world rule object")
            result["plot_threads"].insert(0, "not a plot thread object")
        return result


def _test_llm_seed_project_ignores_malformed_metadata_items(self):
    with tempfile.TemporaryDirectory() as tmp:
        project = LLMNovelWorkflow(MalformedSeedMetadataLLMClient()).run_seed_project(
            NovelRequest(
                title="external smoke",
                premise="external prompt may make the model return loose list items",
                genre="test",
                style="test",
            ),
            Path(tmp),
        )

        self.assertEqual(len(project.characters), 1)
        self.assertEqual(len(project.volume_outline), 1)
        self.assertEqual(len(project.chapter_outlines), 1)
        self.assertEqual(len(project.world_rules), 1)
        self.assertEqual(len(project.plot_threads), 1)


LLMNovelWorkflowTests.test_llm_seed_project_ignores_malformed_metadata_items = (
    _test_llm_seed_project_ignores_malformed_metadata_items
)


def _test_llm_workflow_ignores_malformed_contract_items(self):
    with tempfile.TemporaryDirectory() as tmp:
        project = NovelWorkflow().run_seed_project(
            NovelRequest(
                title="星诊所",
                premise="病历会提前写下尚未发生的症状",
                genre="近未来悬疑",
                style="克制",
            ),
            Path(tmp),
        )

        plan = LLMNovelWorkflow(MalformedContractLLMClient()).plan_next_chapter(project)

        self.assertEqual(
            plan.narrative_contract["plot_thread_progression"],
            ["PT-001 developed"],
        )


LLMNovelWorkflowTests.test_llm_workflow_ignores_malformed_contract_items = (
    _test_llm_workflow_ignores_malformed_contract_items
)


def _test_llm_workflow_normalizes_loose_progression_status(self):
    with tempfile.TemporaryDirectory() as tmp:
        project = NovelWorkflow().run_seed_project(
            NovelRequest(
                title="星诊所",
                premise="病历会提前写下尚未发生的症状",
                genre="近未来悬疑",
                style="克制",
            ),
            Path(tmp),
        )

        LLMNovelWorkflow(LooseProgressionLLMClient()).plan_next_chapter(project)

        self.assertEqual(project.plot_threads[0].status, "developed")


LLMNovelWorkflowTests.test_llm_workflow_normalizes_loose_progression_status = (
    _test_llm_workflow_normalizes_loose_progression_status
)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
from pathlib import Path

from novelagent import OpenAICompatibleClient

from .core import StoryQualityEvaluator, load_evalset
from .judges import QwenStoryJudge


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evaluation.run_eval")
    parser.add_argument("--evalset", required=True, help="评测集 JSON 路径。")
    parser.add_argument("--out-dir", required=True, help="评测结果输出目录。")
    parser.add_argument(
        "--workflow",
        choices=["baseline", "llm"],
        default="baseline",
        help="被测 workflow：baseline 为确定性流程，llm 为大模型写作流程。",
    )
    parser.add_argument(
        "--judge",
        choices=["none", "qwen"],
        default="none",
        help="软质量 Judge：none 不启用，qwen 使用 DashScope 兼容接口。",
    )
    parser.add_argument(
        "--case-id",
        help="只运行指定 case，便于调试真实 LLM/Judge 链路。",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cases = load_evalset(Path(args.evalset))
    if args.case_id:
        cases = [case for case in cases if case.id == args.case_id]
        if not cases:
            raise SystemExit(f"找不到 case-id：{args.case_id}")
    judge = QwenStoryJudge(OpenAICompatibleClient()) if args.judge == "qwen" else None
    reports = StoryQualityEvaluator(
        workflow_mode=args.workflow,
        judge=judge,
    ).evaluate_all(cases, Path(args.out_dir))
    passed = sum(1 for report in reports if report.passed)
    print(f"Story quality eval: {passed}/{len(reports)} cases passed.")
    return 0 if passed == len(reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())

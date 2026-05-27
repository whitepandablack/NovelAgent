from __future__ import annotations

import argparse
from pathlib import Path

from .core import StoryQualityEvaluator, load_evalset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m evaluation.run_eval")
    parser.add_argument("--evalset", required=True, help="评测集 JSON 路径。")
    parser.add_argument("--out-dir", required=True, help="评测结果输出目录。")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cases = load_evalset(Path(args.evalset))
    reports = StoryQualityEvaluator().evaluate_all(cases, Path(args.out_dir))
    passed = sum(1 for report in reports if report.passed)
    print(f"Story quality eval: {passed}/{len(reports)} cases passed.")
    return 0 if passed == len(reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())

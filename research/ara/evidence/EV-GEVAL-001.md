# EV-GEVAL-001: G-Eval rubric-based LLM judge

## Source

- Title: G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment
- URL: https://arxiv.org/abs/2303.16634
- ACL page: https://aclanthology.org/2023.emnlp-main.153/

## Evidence Summary

G-Eval uses task-specific rubrics and chain-of-thought style evaluation steps with GPT-4 to score NLG outputs, and reports stronger correlation with human judgment than classic overlap metrics on summarization and dialogue tasks.

## Implication For NovelAgent

LLM judge evaluation is appropriate for soft dimensions such as style, scene vividness, and character believability, but it should sit above deterministic hard checks rather than replace them. NovelAgent should keep model-independent evals for continuity, state transitions, and regression safety.

## Claims Supported

- C3

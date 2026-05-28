# EV-SWEBENCH-001: SWE-bench task-grounded agent evaluation

## Source

- Title: SWE-bench: Can Language Models Resolve Real-World GitHub Issues?
- URL: https://arxiv.org/abs/2310.06770
- Project page: https://www.swebench.com/original.html

## Evidence Summary

SWE-bench frames evaluation as resolving real GitHub issues in a codebase, with success judged by whether the resulting patch satisfies tests. The key pattern is not free-form output scoring; it is task execution against a fixed state and externally checkable outcome.

## Implication For NovelAgent

NovelAgent evals should treat story generation as stateful project work: given a story bible, outline, timeline, and draft state, the agent performs a creative operation and the evaluator checks the resulting state delta.

## Claims Supported

- C1
- C4

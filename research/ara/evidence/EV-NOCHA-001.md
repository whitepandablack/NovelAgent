# EV-NOCHA-001: NoCha narrative minimal pairs

## Source

- Title: One Thousand and One Pairs: A "novel" challenge for long-context language models
- URL: https://arxiv.org/abs/2406.16264
- Project page: https://novelchallenge.github.io/

## Evidence Summary

NoCha evaluates long-context narrative understanding with 1,001 minimally different true/false claim pairs about 67 recently published fiction books. The benchmark reports that models do better on sentence-level retrieval than on global reasoning, explanations can be unreliable even when labels are correct, and speculative fiction with extensive world-building is especially difficult.

## Implication For NovelAgent

NovelAgent should keep minimal-pair tests as a first-class eval family, but make them harder than keyword overlap. Holdout pairs should include near-miss claims where the wording is similar and the difference is causal, temporal, or state-based.

## Claims Supported

- C2
- C5

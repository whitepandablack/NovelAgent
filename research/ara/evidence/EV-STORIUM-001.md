# EV-STORIUM-001: STORIUM story generation platform

## Source

- Title: STORIUM: A Dataset and Evaluation Platform for Machine-in-the-Loop Story Generation
- URL: https://arxiv.org/abs/2010.01717
- Platform page: https://storium.cs.umass.edu/

## Evidence Summary

STORIUM highlights that long-form story generation is difficult to evaluate because outputs are open-ended and automatic/crowdsourced evaluations can be unreliable. Its dataset includes rich story context and character annotations, and its evaluation platform observes how real authors query and edit generated continuations.

## Implication For NovelAgent

Story evals need structured context, character goals, and revision/edit signals. A quality system should combine deterministic state checks with later human or LLM preference review, rather than claiming that a single score guarantees good fiction.

## Claims Supported

- C3
- C5

# ARA Pre-Level-2 Review

Date: 2026-05-28

## Verdict

当前 `research/ara` 还不能进入正式 ARA Seal Level 2 审查。它已经记录了问题、核心 claims、实验草案和探索树，但缺少 Level 1 所需的完整结构与可追溯证据层。

建议判定：**Needs Structural Completion Before Level 2**。

## Read Order

1. `research/ara/logic/problem.md`
2. `research/ara/logic/claims.md`
3. `research/ara/logic/experiments.md`
4. `research/ara/exploration-tree.md`
5. `research/literature/survey.md`
6. `research/findings.md`
7. `research/research-log.md`
8. `evaluation/results/story_quality_results.json`

## Dimension Scores

| Dimension | Score | Rationale |
|---|---:|---|
| Evidence Relevance | 3/5 | Claims point to plausible sources such as NoCha, G-Eval, SWE-bench and AgentBench, but evidence is still survey-level and not captured as source-specific evidence objects. |
| Falsifiability Quality | 3/5 | Experiments are directional and executable evals now exist, but claims do not yet define clear falsification thresholds across multiple projects or generators. |
| Scope Calibration | 2/5 | The language sometimes implies a general story-agent evaluation system, while current evidence only covers one seed project, one deterministic workflow, and five small cases. |
| Argument Coherence | 4/5 | The arc is coherent: fixed story state -> eval cases -> failures -> workflow improvements -> improved scores. |
| Exploration Integrity | 3/5 | Research log captures failures and pivots, including 2/3, 3/5, and 5/5 eval milestones, but dead ends and alternatives are not yet represented in a structured trace. |
| Methodological Rigor | 2/5 | The eval is reproducible and test-backed, but sample size, scorer validity, rubric calibration, and external baselines are still weak. |

Overall: **Weak Reject for publication-grade ARA; useful internal research artifact.**

## Strengths

- The project now has an executable eval loop rather than only qualitative discussion.
- The eval has already exposed real weaknesses: shallow beat mention and append-only revision.
- The workflow improvement was measured by the same fixed cases, moving from `3/5` to `5/5`.
- The research direction is grounded in relevant benchmark families: long-context minimal pairs, agent benchmarks, LLM-as-judge, and software-style regression evaluation.

## Critical Issues

### 1. Evidence is not yet captured at ARA granularity

`claims.md` cites NoCha, G-Eval, SWE-bench and AgentBench at a high level, but there are no evidence files with exact paper metadata, extracted claims, tables, methodology notes, or links from claims to evidence IDs.

Required fix:

- Add `research/ara/evidence/` files for each key source.
- Give each evidence item a stable ID such as `EV-NOCHA-001`.
- Update claims to cite those IDs.

### 2. The eval may be overfit to `星诊所`

All executable cases currently target one deterministic project and one deterministic generator. The `5/5` result proves improvement on this micro-benchmark, but not general story-writing ability.

Required fix:

- Add at least one second project with different genre and constraints.
- Add adversarial or held-out cases not used while improving the workflow.
- Track scores separately for development and holdout evalsets.

### 3. Scoring scales are inconsistent

Most scores are 0-100, while `beat_grounding` uses a 0-5 scale with `pass_threshold=4`. This is acceptable internally but makes total score comparisons confusing.

Required fix:

- Normalize all case-level scores to 0-100 in reports.
- Preserve raw subscore fields such as `raw_beat_grounding=5`.

### 4. Revision quality is still a heuristic

`revision_quality=80` mainly checks that the text avoids `修订补充：` and contains scene markers. This is better than append-only revision but still too shallow for real revision quality.

Required fix:

- Add checks for whether each original review issue is semantically resolved.
- Add non-regression checks for chapter summary, referenced characters, timeline, and plot thread status.
- Add a soft judge rubric later for readability, continuity, and emotional plausibility.

### 5. Minimal pairs are too easy

The current minimal pairs are close to direct keyword matching. This tests plumbing more than deep narrative memory.

Required fix:

- Add pairs that require combining character card + chapter event + plot thread.
- Add near-miss false statements that share many keywords but violate causality or chronology.
- Require evidence pointers to concrete project fields.

## Recommended Next Steps

1. Complete ARA structure before formal Level 2:
   - `PAPER.md`
   - `logic/concepts.md`
   - `logic/solution/architecture.md`
   - `logic/solution/algorithm.md`
   - `logic/solution/constraints.md`
   - `logic/related_work.md`
   - `evidence/`
   - `trace/exploration_tree.yaml`

2. Add second-wave eval cases:
   - `character_arc_consistency`
   - `plot_thread_progression`
   - `timeline_causality`
   - harder `minimal_pairs`

3. Split evalsets:
   - `star_clinic_dev.json`
   - `star_clinic_holdout.json`
   - future cross-genre evalset

4. Normalize scoring:
   - all report totals should be 0-100
   - raw metric values should be preserved separately

5. Re-run rigor review after Level 1 structure is complete.


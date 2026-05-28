# Story Quality Eval Results

## star_clinic_plan_chapter_02: PASS

- Total: 100/100
- Scores: {'hard_constraints': 100}
- Raw scores: {}

## star_clinic_beat_grounding: PASS

- Total: 80/100
- Scores: {'beat_grounding': 80}
- Raw scores: {'beat_grounding': 4}

## star_clinic_revision_non_regression: PASS

- Total: 100/100
- Scores: {'hard_constraints': 100}
- Raw scores: {}

## star_clinic_minimal_pairs: PASS

- Total: 100/100
- Scores: {'minimal_pair_accuracy': 100}
- Raw scores: {}

## star_clinic_revision_quality: PASS

- Total: 80/100
- Scores: {'revision_quality': 80}
- Raw scores: {}

## star_clinic_character_arc_consistency: FAIL

- Total: 0/100
- Scores: {'character_arc_consistency': 0}
- Raw scores: {}
- Findings:
  - [error] character_arc_consistency: 人物行动没有足够体现 goal/conflict/arc。

## star_clinic_plot_thread_progression: FAIL

- Total: 50/100
- Scores: {'plot_thread_progression': 50}
- Raw scores: {}
- Findings:
  - [error] plot_thread_progression: PT-001 没有从重复提及推进到 developed 状态。
  - [error] plot_thread_progression: PT-001 没有记录第 2 章的推进。

## star_clinic_timeline_causality: FAIL

- Total: 50/100
- Scores: {'timeline_causality': 50}
- Raw scores: {}
- Findings:
  - [error] timeline_causality: 时间线摘要没有记录可审计的因果连接。

## star_clinic_harder_minimal_pairs: FAIL

- Total: 50/100
- Scores: {'minimal_pair_accuracy': 50}
- Raw scores: {}
- Findings:
  - [error] minimal_pair_accuracy: 叙事 minimal-pair 准确率为 50%。

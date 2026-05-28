# Algorithm Notes

## Percent Scale Normalization

All reported scores use 0-100.

- Hard checks: start at 100 and subtract 25 per error.
- Beat grounding: keep raw 0-5 in raw_scores.beat_grounding, report raw * 20.
- Accuracy checks: report correct / total * 100.

## Pass Semantics

A report passes only when:

1. no finding has severity=error, and
2. total_score >= pass_threshold.

All pass_threshold values are interpreted on the 0-100 scale.

## Holdout Semantics

Holdout failures are allowed and should be reported as current capability boundaries. They are not failures of the test suite unless a test expected a specific boundary and it disappears without a corresponding implementation plan.

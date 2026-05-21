# NovelAgent v0.2 Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local-first long-form writing engine and CLI workbench for NovelAgent v0.2.

**Architecture:** Extend the existing dataclass models and JSON project persistence, then add deterministic workflow methods that the CLI can call. Keep all generation provider-neutral and fully covered by local `unittest` tests.

**Tech Stack:** Python 3.11+, standard library dataclasses, JSON persistence, argparse, unittest.

---

### Task 1: Structured Long-Form Memory Models

**Files:**
- Modify: `src/novelagent/models.py`
- Modify: `src/novelagent/project.py`
- Modify: `src/novelagent/__init__.py`
- Test: `tests/test_project.py`

- [ ] Add failing tests proving world rules, timeline events, plot threads, chapter plans, and revision tasks persist through save/load.
- [ ] Run `python -m unittest tests.test_project -v` and confirm the new test fails because fields/classes are missing.
- [ ] Add dataclasses and project fields, preserving compatibility with existing project JSON.
- [ ] Export new models from `novelagent.__init__`.
- [ ] Re-run `python -m unittest tests.test_project -v` and confirm it passes.

### Task 2: Planning and Drafting Workflow

**Files:**
- Modify: `src/novelagent/workflow.py`
- Test: `tests/test_workflow.py`

- [ ] Add failing tests for `plan_next_chapter` and `draft_next_chapter`.
- [ ] Run `python -m unittest tests.test_workflow -v` and confirm failures are for missing methods/behavior.
- [ ] Implement deterministic next-chapter planning that avoids duplicate plans.
- [ ] Implement deterministic next-chapter drafting that records source plan number and timeline event.
- [ ] Re-run `python -m unittest tests.test_workflow -v` and confirm it passes.

### Task 3: Expanded Review and Revision Workflow

**Files:**
- Modify: `src/novelagent/review.py`
- Modify: `src/novelagent/workflow.py`
- Test: `tests/test_review.py`
- Test: `tests/test_workflow.py`

- [ ] Add failing tests for missing beat coverage, duplicate chapter numbers, revision task creation, and revision completion.
- [ ] Run targeted tests and confirm expected failures.
- [ ] Expand `ContinuityChecker` to inspect chapter plans, duplicate chapter numbers, and beat coverage.
- [ ] Add workflow methods to create revision tasks and apply deterministic revisions.
- [ ] Re-run review and workflow tests and confirm they pass.

### Task 4: CLI Workbench Commands

**Files:**
- Modify: `src/novelagent/cli.py`
- Test: `tests/test_cli.py`

- [ ] Add failing tests for `status`, `plan-next`, `draft-next`, `review`, `revise`, and `export`.
- [ ] Run `python -m unittest tests.test_cli -v` and confirm missing command failures.
- [ ] Implement commands with Chinese output and non-zero failures for invalid project/chapter paths.
- [ ] Re-run CLI tests and confirm they pass.

### Task 5: Full Verification

**Files:**
- Modify: `README.md`

- [ ] Update README with v0.2 CLI workflow examples.
- [ ] Run `python -m unittest discover -v`.
- [ ] Confirm all tests pass.


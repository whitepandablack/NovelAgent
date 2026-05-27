# Experiments

## E1：StoryEvalCase schema pilot

构建 3 个固定 eval case，覆盖下一章规划、minimal-pair 伏笔判断和修订不回归。

Prediction：规则评分能稳定捕捉当前 workflow 的至少两类缺陷：beat 浅覆盖和修订追加式补丁。

## E2：Beat grounding scorer

为 `矛盾记忆` 这类抽象 beat 建立 0-5 分评分规则，比较当前模板生成和后续 LLM 生成。

Prediction：当前 deterministic generator 只能达到 mention 或解释层级，无法达到场景化 grounding。

## E3：Revision non-regression test

给定一个缺失 beat 的章节，要求修订后既修复问题又不改变时间线和 plot thread 状态。

Prediction：当前修订流程会通过部分硬检查，但在文本质量和真实重写能力上明显不足。


# EV-AGENTBENCH-001: AgentBench multi-environment evaluation

## Source

- Title: AgentBench: Evaluating LLMs as Agents
- URL: https://arxiv.org/abs/2308.03688
- GitHub: https://github.com/THUDM/AgentBench

## Evidence Summary

AgentBench evaluates LLM agents across multiple interactive environments and identifies long-term reasoning, decision-making, and instruction-following as major bottlenecks for usable agents.

## Implication For NovelAgent

NovelAgent should not rely on one short generation sample. The eval framework needs multiple task families that test planning, drafting, revision, timeline updates, and memory/state maintenance under separate workflows.

## Claims Supported

- C1
- C4

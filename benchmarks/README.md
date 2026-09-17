# Benchmarks

The benchmark layer measures whether myAI is actually better than a strong frontier-model baseline.

## Public vs private benchmark material

This repository is public. Therefore **real hidden benchmark truth must never be committed here**.

Public benchmark code may define:

- schemas for benchmark cases;
- evaluator interfaces;
- scoring logic that does not reveal answers;
- toy/example cases;
- tooling for loading local or CI-injected private benchmark packs.

Private benchmark material belongs under `benchmarks/private/` (gitignored) or in a separate private repository / secure artifact store. It may contain:

- true opportunity rankings;
- hidden workflow costs and frequencies;
- policy edge cases;
- intervention acceptance cases;
- adversarial/contradictory evidence cases;
- randomized fixture seeds not exposed to the runtime agent.

## Why this boundary matters

If development agents can read the benchmark answers, the experiment is contaminated: the system may appear to reason correctly while simply encoding the expected results. The runtime system must see only the same observable company evidence that the baseline receives.

The first real benchmark pack should be created before implementing the structured opportunity engine, so later architectural work is evaluated against a frozen target rather than a moving test.

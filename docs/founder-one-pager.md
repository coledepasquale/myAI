# myAI — Founder One-Pager

**Working thesis:** AI modernization should become a closed-loop product, not a consulting deck.

## The problem

Businesses increasingly know that AI matters, but many still do not know where it will create material value, how to adapt it to their actual workflows, how to implement it safely, or how to prove that an intervention worked.

The implementation cost of software is collapsing faster than the difficulty of answering the higher-level question: **what should this organization change, and why?**

## The product vision

myAI aims to become an **AI modernization autopilot**:

> Understand an organization → identify high-value opportunities → substantiate them with evidence → build a candidate intervention → evaluate it safely → ask for approval → measure the result → repeat.

The goal is not to produce recommendations. The goal is to produce **measurable business improvements**.

## Why now

Frontier models can already write software, operate computers, reason across documents, and use tools. That gives tiny teams leverage that previously required large consulting and engineering organizations. At the same time, research and market activity show that AI adoption is broad but deep integration and ROI measurement remain immature.

A new category is forming around AI transformation. That is validation, not proof that the opportunity is closed.

## Competitive reality

The market is early but active.

- **Within (formerly Klarity)** is the strongest horizontal threat: it maps how organizations work, identifies AI opportunities, and builds agents. It is much larger and better funded than the newest entrants, but its broad "company brain / AI transformation" positioning is recent.
- **Foaster, Ontora, Marker, Terminal Use, Autostep, Sona8, and Trace** are young AI-native companies attacking pieces of discovery, process mapping, implementation, and transformation. Many are teams of only one to four people.
- **Workhelix** focuses on AI opportunity/ROI measurement.
- **Celonis and UiPath** bring mature process intelligence / task mining and enterprise distribution.
- **Accenture and other consultancies** validate enormous willingness to spend on AI transformation, but their delivery model is labor-heavy.

The important conclusion is: **we are not first, but the category does not appear settled.** Engineering speed alone will not win; differentiated product architecture and distribution must emerge.

## Our proposed differentiation

Most current approaches emphasize one or more of:

1. discovering workflows;
2. interviewing employees;
3. identifying automation opportunities;
4. producing transformation roadmaps;
5. deploying custom agents with forward-deployed engineers.

The technical thesis we want to test is one step further:

> Can a system close the loop from evidence to intervention to objective evaluation with materially less human consulting?

That means the defensible layer would not be "we have better prompts." It would be the accumulated machinery and data around company modeling, evidence provenance, opportunity calibration, intervention generation, safe evaluation, outcome measurement, and eventually repeated transformation trajectories.

## The experiment

We are starting with a controlled synthetic company, **Northstar Industrial Services**, rather than a live customer.

We will compare:

**Control:** frontier model + all allowed company context + an excellent one-shot prompt.

**myAI:** evidence store + explicit company/workflow model + opportunity reasoning + critique/calibration + bounded implementation + sandbox evaluation.

If our structured system does not materially outperform the control, we simplify or stop.

## What success looks like

A compelling POC would be able to say something like:

> "I found 37 modernization opportunities. These five are high confidence. The top one is supported by specific workflow evidence, is worth approximately $X/year under explicit assumptions, and I have already built and tested a candidate intervention. It passes hidden policy/correctness cases and materially improves cycle time/cost."

Then it should transfer to a second company without rewriting the core architecture.

## What we are *not* doing yet

- no proprietary foundation model;
- no generic agent platform;
- no polished SaaS dashboard;
- no autonomous production deployment;
- no vertical lock-in;
- no months of infrastructure before proving differentiated intelligence.

## Near-term plan

**M0 — Foundation:** typed domain model, evidence provenance, provider-independent LLM interface, synthetic company fixture, reproducible runs, CLI, tests, CI.

**M1 — Baseline:** execute and persist repeated frontier-model baseline runs.

**M2 — Company model:** infer explicit workflows/systems/relationships from evidence.

**M3 — Opportunity engine:** generate, challenge, substantiate, rank, and calibrate modernization opportunities.

**M4/M5 — Closed loop:** implement one bounded intervention and evaluate it against hidden cases and business proxies.

**M6 — Generalization:** repeat on a second synthetic company without changing the core abstractions.

## Decision rule

This project earns more time only when the evidence improves.

If the intelligence reduces to "Claude with a good prompt," if every customer would require bespoke engineering, or if interventions cannot be evaluated objectively, we should stop or radically simplify.

If the system reliably finds important opportunities that the baseline misses, grounds them in evidence, builds safe interventions, and measures improvement, then we have earned the right to test it with real organizations.

**Current stance (September 2026): build the POC; do not yet build the company.**

# myAI POC Charter v0.1

## Mission

Test whether a structured, evidence-grounded AI modernization system can discover, justify, implement, and evaluate high-value business improvements **materially better than a strong one-shot frontier-model baseline**.

The long-term product vision is a closed loop:

1. Understand an organization.
2. Model how work actually happens.
3. Identify high-value modernization opportunities.
4. Substantiate each opportunity with evidence, assumptions, and confidence.
5. Build a candidate intervention safely.
6. Evaluate it in a sandbox against explicit business objectives and constraints.
7. Ask for approval where required.
8. Measure outcomes and repeat.

## What this POC is not

- Not an AI consulting report generator.
- Not a generic chatbot over company documents.
- Not a website builder.
- Not a process-mining clone.
- Not a reason to train a proprietary foundation model before a demonstrated capability gap exists.
- Not an autonomous production deployment system.

## Core hypothesis

Given incomplete but realistic information about a company and its objectives, a structured system with explicit evidence provenance, workflow modeling, opportunity ranking, implementation, and evaluation will outperform:

> frontier model + the same company context + a carefully engineered one-shot prompt.

If that hypothesis does not hold, the architecture should be simplified or the project should be stopped.

## Experimental environment

The first controlled environment is **Northstar Industrial Services**, a fictional ~80-person company with realistic departments, systems, policies, documents, workflows, and hidden benchmark ground truth.

The runtime system sees only the evidence made available to it. Hidden benchmark data is kept separate and is used only by the evaluator.

Seeded opportunity classes include:

- quote preparation and approval;
- support intake/routing;
- weekly operational reporting;
- procurement exceptions;
- repeated internal policy questions;
- deliberately attractive but low-value decoys.

Northstar is an experimental fixture, not a vertical-market commitment.

## Design principles

### 1. Baseline before architecture
Freeze and run a strong one-shot baseline before adding multi-step reasoning or agents.

### 2. Evidence before assertion
Claims about cost, frequency, bottlenecks, or ROI must cite evidence IDs and expose assumptions.

### 3. Structured objects over prose
Core system boundaries exchange typed domain objects, not unconstrained text.

### 4. Provider independence
Domain code must not depend on a particular LLM vendor.

### 5. Reproducibility
Every model run records provider, model, prompt/template version, inputs, outputs, timing, token usage when available, and cost when available.

### 6. Sandbox first
Generated interventions are evaluated in controlled environments. No real company may be modified autonomously in this POC.

### 7. Train only against demonstrated gaps
Fine-tuning/distillation/custom models are valid future tools, but only after benchmark evidence identifies a repeatable limitation and sufficient trajectories exist.

### 8. Horizontal architecture
No industry-specific assumptions belong in the core domain model. Environment-specific adapters and fixtures may be vertical.

## Primary benchmark questions

1. Does the system identify the highest-value hidden opportunities?
2. Are its claims grounded in evidence?
3. Are estimated value and confidence calibrated?
4. Does it avoid high-confidence recommendations when evidence is weak or contradictory?
5. Can it generate an intervention that improves the target workflow in a sandbox?
6. Does the same core architecture transfer to a second synthetic company without bespoke core-code changes?
7. Does the structured system materially outperform the one-shot frontier-model baseline?

## Kill criteria

Stop, simplify, or rethink the thesis if any of the following persist after the initial experiment:

- A strong one-shot model performs essentially as well as the structured system.
- The majority of useful intelligence comes from manually encoded benchmark answers.
- Opportunity discovery requires substantial bespoke engineering per company.
- Evidence provenance does not improve recommendation quality or trustworthiness.
- Implementation cannot be evaluated objectively enough to support a closed loop.
- Generalization to a second company requires rewriting the core architecture.

## Initial milestones

### M0 — Foundation
Typed domain model, provider abstraction, run records, evidence store, fixture loader, CLI, tests, CI.

### M1 — Baseline
Run the same one-shot baseline repeatedly against Northstar and persist structured results.

### M2 — Company model
Build explicit systems/workflows/evidence relationships without leaking benchmark ground truth.

### M3 — Opportunity engine
Generate, critique, substantiate, rank, and calibrate opportunities.

### M4 — Intervention
Implement one bounded improvement inside the sandbox.

### M5 — Evaluation
Compare original vs modified workflow on hidden cases and publish a benchmark report.

### M6 — Generalization
Add a second company fixture without changing the core domain abstractions.

## Success bar for v0.1

We should be able to point to a reproducible run where the system:

- correctly identifies a high-value hidden opportunity;
- shows the evidence and assumptions used;
- ranks it materially better than the baseline;
- builds a bounded intervention;
- passes hidden correctness/policy tests;
- demonstrates measurable improvement on a business proxy;
- repeats the process across randomized fixture variants.

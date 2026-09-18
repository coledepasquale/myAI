# myAI Project State and Continuation Handoff

**Last updated:** 2026-09-17 (M1.5 benchmark framework)  
**Purpose:** This is the canonical handoff for a new human, coding agent, or LLM session. It records why the project exists, what research has already been done, what has been built, what experiments have run, what conclusions are and are not justified, and the exact next implementation sequence.

---

## 1. Project thesis

myAI is an experimental **AI modernization autopilot**.

The product thesis is not “AI consulting with better prompts” and not “a chatbot over company documents.” The long-term loop is:

> Understand a company → model how work actually happens → discover high-value AI/software opportunities → substantiate them with evidence and assumptions → build a candidate intervention → evaluate it safely → request approval where needed → measure outcome → learn and repeat.

The deeper abstraction is:

> environment + objective → understand state → act → measure reward → learn → repeat.

Applied to business software:

> company + objective → understand workflows → change the system → measure outcome → learn → repeat.

The POC exists to test whether this structured loop adds measurable intelligence beyond simply giving a frontier model all available company context and a very good one-shot prompt.

### Governing falsification rule

If a strong frontier model given the same observable context performs essentially as well as the structured system, **do not rationalize the extra architecture**. Simplify the thesis, narrow the wedge, or stop.

See [`../POC_CHARTER.md`](../POC_CHARTER.md) for the formal charter and kill criteria.

---

## 2. How the idea evolved

The project began from a general-agent idea: software that can observe an environment, infer controls, act repeatedly, optimize an objective, and improve from feedback. The original example involved games/GUI environments, but real-money gambling automation was rejected as a product direction because of platform/legal constraints.

The useful abstraction survived: create software that can understand a complex environment, choose actions, measure outcomes, and improve.

The project then explored self-improving websites and GUI/software optimization. Desk research showed that AI website generation, CRO, self-improving websites, browser agents, and RL environments are already active categories. That ruled out an undifferentiated “AI website optimizer” thesis.

The broader opportunity became **AI business modernization**: given a business, its software, workflows, constraints, and objectives, determine what should change, implement bounded improvements, and prove the result.

The key proposed differentiation is therefore not discovery alone, interviews alone, task mining alone, recommendations alone, or custom agent development alone. It is the **closed loop from evidence → recommendation → intervention → objective evaluation → measured outcome**.

---

## 3. Market research already completed

Do not repeat generic market research before reading [`research/market-landscape.md`](research/market-landscape.md).

The research established three important things:

1. **Demand exists.** Businesses are adopting AI rapidly, but deep integration, implementation, adaptation to business context, data quality, security, and ROI measurement remain major gaps.
2. **Businesses spend on the problem.** Enterprise consulting, AI transformation programs, process intelligence, and AI implementation all demonstrate willingness to pay.
3. **The category is active but not settled.** There is a meaningful group of young AI-native companies plus mature adjacent platforms, but no evidence that the horizontal “continuous AI modernization autopilot” category has a definitive winner.

Important competitors/adjacencies already researched include:

- Within (formerly Klarity) — strongest scaled horizontal threat; Company Brain / AI transformation positioning.
- Foaster — AI-native consulting/discovery via employee interviews.
- Ontora — discovery/context layer for AI transformation.
- Marker — FDE-heavy enterprise agent modernization.
- Autostep — knowledge-work P&L / repetitive-work discovery.
- Cerenovus — AI operating partner / value-creation discovery.
- Terminal Use — operations-heavy transformation.
- Sona8 — interview/process mapping and change tracking.
- Trace — human/AI workflow orchestration.
- Workhelix — AI opportunity and ROI measurement.
- UiPath Task Mining and Celonis — mature process/task intelligence adjacencies.
- Major consultancies / forward-deployed engineering models — validate spend but often remain labor-heavy.

Strategic conclusion: **do not differentiate on “we interview employees,” “we observe work,” “we rank automation tasks,” or “we can build agents.”** Competitors already do those things. The technical experiment should test whether the closed-loop architecture provides a defensible advantage.

The working customer band, if the POC earns real-world testing, is likely roughly **20–500 employees**: enough process volume and budget to matter, but often without a large internal AI platform team. This is a hypothesis, not a committed vertical.

---

## 4. Current product/technical strategy

The system should remain horizontal at its core. Verticalization, if it happens, should initially be a GTM/data decision rather than a hard-coded architecture decision.

The intended eventual pipeline is:

```text
company context
    ↓
evidence/provenance layer
    ↓
company/workflow model
    ↓
opportunity generation
    ↓
skeptic / evidence challenge
    ↓
ROI + feasibility + risk ranking
    ↓
intervention builder
    ↓
sandbox evaluator
    ↓
human approval boundary
    ↓
measured outcome
    ↓
learning / repeated modernization
```

The hypothesized moat is not a foundation model. It is the accumulated trajectory data and machinery around:

> company state → recommendation → intervention → outcome

with explicit evidence, policy constraints, and measured ROI.

A proprietary model, fine-tune, distilled planner, or ranker is only justified later if repeated benchmark failures reveal a stable capability gap and there is enough proprietary trajectory data to train against it.

---

## 5. Repository and implementation status

Repository: `coledepasquale/myAI`.

The repository is **public**. Treat anything committed here as public information.

### Merged work

#### PR #1 — Foundation v0.1
Merged into `main` on 2026-09-17.

Implemented:

- POC charter and explicit kill criteria.
- Python 3.12 project configuration.
- Pydantic typed domain objects.
- provider-independent `StructuredModel` boundary.
- in-memory evidence provenance store.
- controlled Northstar synthetic-company fixture.
- one-shot baseline prompt/request builder.
- CLI inspection/context commands.
- Ruff, Mypy, Pytest, and GitHub Actions CI.
- founder one-pager, market research, ADRs, benchmark public/private policy.
- `.env` / runs / artifacts / private benchmark ignore rules.

#### PR #2 — M1 Anthropic baseline experiment runner
Merged into `main` on 2026-09-17.

Implemented:

- Anthropic Python SDK dependency.
- Anthropic provider adapter behind the existing provider-neutral model gateway.
- schema-constrained Pydantic output.
- removal of the false assumption that every provider/model accepts portable `temperature` controls.
- `myai baseline` CLI command.
- immutable local run artifacts under `runs/`.
- model, prompt version, input hash, token counts, latency, estimated cost, opportunity count, and evidence-citation validity metadata.
- tests for baseline hashing, pricing, persistence, and settings behavior.
- no live API calls in CI.

#### PR #3 — Anthropic workspace selection fix
Merged into `main` on 2026-09-17.

The first live request revealed that the user’s Anthropic API key was organization/multi-workspace scoped rather than bound to one workspace. Anthropic returned HTTP 400 requiring the `anthropic-workspace-id` header.

The code now supports optional local:

```text
ANTHROPIC_WORKSPACE_ID=wrkspc_...
```

and injects `anthropic-workspace-id` only when configured. Workspace-scoped keys continue to work without it.

#### M1.5 — Public benchmark/evaluator framework
Implemented 2026-09-17 (see §12 Step 2).

Implemented:

- `BenchmarkCase` / `CaseAnswerKey` as **separate types**, so observable input and hidden truth cannot be serialized together into a prompt.
- `BenchmarkPack` with completeness validation (every case has exactly one answer; every referenced category exists) and a SHA-256 `pack_hash` for freezing.
- deterministic keyword-based opportunity classification (no LLM judge — see ADR 0002).
- the full v0.1 scorecard: top-1, top-3 recall, Spearman rank correlation, decoy promotion, evidence-citation validity, unsupported ROI, ROI band coverage/calibration, policy detection, critical policy violations, confidence Brier score.
- `BenchmarkPackLoader` contract plus a filesystem loader reading `benchmarks/private/` or `MYAI_BENCHMARK_PACK`.
- report aggregation with pack version/hash stamping and top-1 stability across repeated runs.
- `myai benchmark-validate`, which summarizes a pack **without printing answers** and exits non-zero if the pack is tracked by Git.
- a committed toy pack under `tests/data/toy_pack/` and 38 deterministic tests. No real answers committed.

Also fixed: `tests/conftest.py` now isolates tests from the developer's local `.env`. Previously `Settings()` silently read the real `.env`, so `test_workspace_id_is_optional_for_scoped_keys` passed in credential-free CI and failed on a configured machine.

### CI state

After the M1 implementation and the workspace fix, Ruff, Mypy, and Pytest pass in GitHub Actions. CI does not require Anthropic credentials and does not make paid model calls. The M1.5 benchmark tests are likewise deterministic and credential-free.

---

## 6. Important current code map

Core files:

- `src/myai/domain.py` — typed domain objects: evidence, assumptions, workflows, opportunities, interventions, evaluations, model invocation/run concepts.
- `src/myai/evidence.py` — minimal in-memory evidence registry with stable IDs/provenance.
- `src/myai/model_gateway.py` — provider-neutral structured-model request/result protocol.
- `src/myai/providers/anthropic.py` — Anthropic implementation and dated cost-estimation table.
- `src/myai/baseline.py` — versioned one-shot baseline prompt, stable input hash, baseline execution.
- `src/myai/run_store.py` — immutable local baseline artifacts.
- `src/myai/settings.py` — local `.env` configuration for Anthropic key/workspace.
- `src/myai/fixtures.py` — fixture loading.
- `src/myai/cli.py` — `inspect`, `dump-context`, and paid `baseline` commands.
- `src/myai/benchmark/schema.py` — benchmark case/answer/pack types and pack hashing.
- `src/myai/benchmark/categories.py` — deterministic prose-to-category matching.
- `src/myai/benchmark/scoring.py` — `CaseScore` and all v0.1 metric functions.
- `src/myai/benchmark/loader.py` — private-pack loader contract and filesystem loader.
- `src/myai/benchmark/report.py` — `CaseRun`, `BenchmarkReport`, aggregation, stability.
- `environments/northstar/` — public observable Northstar company/evidence fixture.
- `tests/data/toy_pack/` — public toy pack with fake answers, used only by tests.
- `benchmarks/README.md` — rules for keeping real benchmark truth out of the public/runtime-visible repo, plus the pack-authoring format.

Do not introduce a graph database just because the future concept is called a “Company Graph.” The first Company Model should remain a logical typed representation unless benchmark/scale evidence creates a real storage need.

---

## 7. Northstar Industrial Services fixture

Northstar is a fictional ~82-person regional B2B industrial-services company. It is deliberately synthetic so the POC can be measured safely and reproducibly.

Observable systems currently include:

- Atlas CRM
- Beacon Desk ticketing
- LedgerPro finance
- Stockroom inventory
- DriveBox document store
- Mail/email

Business objectives currently include:

- reduce avoidable labor without degrading quality;
- shorten customer response time;
- preserve policy/approval controls;
- increase operational visibility.

### Current observable evidence

The public fixture contains eight evidence records:

1. Sales quote workflow: CRM → inventory → pricing workbook → discount policy → proposal → manager approval for larger discounts; routine preparation roughly 20–25 minutes.
2. 1,382 quote requests in the trailing 12 months.
3. Discount approval policy: <=5% account owner; >5% to <=12% sales manager; >12% VP Sales; required approval must be recorded before a customer-facing quote.
4. Support agents manually triage inbound requests; most are fast, but unusual multi-site cases need judgment.
5. ~860 support tickets/month; median first response 34 minutes; median triage 1.6 minutes.
6. Finance analyst spends roughly four hours each Friday collecting/formatting weekly operations-report data from three systems.
7. Procurement exceptions are uncommon but high consequence and may involve qualification, insurance, legal review, and variable policy.
8. Employees frequently search travel/expense/leave/equipment policies (~310 searches/month), but no reliable current measure of human-support cost exists.

This observable data is **not** the hidden answer key. Runtime systems and baselines may see it.

---

## 8. What the baseline experiment actually is

The baseline is the control condition for the startup thesis.

It gives one frontier model:

- Northstar company metadata/objectives;
- exactly the observable evidence records;
- a versioned one-shot system prompt.

The prompt asks the model to identify/rank AI/software modernization opportunities, use only supplied evidence, cite evidence IDs, expose assumptions, and prioritize expected business value, confidence, feasibility, and implementation cost.

The baseline does **not** receive:

- a Company Graph;
- workflow reconstruction generated by myAI;
- multi-agent debate;
- a hidden benchmark answer key;
- private ROI truth;
- intervention-building tools;
- a sandbox evaluator.

This is intentional: our future system must earn its complexity by outperforming this control on the same observable information.

Each successful baseline run writes a local, git-ignored directory containing:

```text
runs/<timestamp>_<uuid>/
    request.json
    output.json
    run.json
```

`request.json` captures the exact request/prompt version, `output.json` contains validated structured opportunities, and `run.json` records reproducibility/operational metadata.

---

## 9. First live experiment history

### First attempt: failed request, useful integration finding

Command:

```bash
myai baseline northstar --model claude-sonnet-5 --runs 1
```

Anthropic returned HTTP 400 because the API key was not scoped to one workspace and therefore required an `anthropic-workspace-id` header.

That integration issue was fixed in PR #3 with optional `ANTHROPIC_WORKSPACE_ID` support.

No model output was produced by the failed request, so it is not an experimental observation.

### First successful end-to-end smoke run

Date: **2026-09-17**  
Model: **`claude-sonnet-5`**  
Prompt: baseline v0.1  
Run directory on the machine that executed it: `runs/20260917T201333Z_6f176fc5-11b4-48f5-a11e-03c69086d149`

Observed ranking:

| Rank | Opportunity | Estimated annual value | Confidence | Feasibility | Evidence |
|---|---|---:|---:|---:|---|
| 1 | Automate Sales Quote Generation and Approval Routing | $15,000 | 55% | 70% | quote observation + quote volume + discount policy |
| 2 | Automate Weekly Finance Operations Report | $9,500 | 60% | 80% | finance weekly-report observation |
| 3 | Automate Routine Support Ticket Triage | $8,000 | 50% | 75% | support observation + support metric |
| 4 | Deploy Self-Service Policy Assistant (Pilot, Value Unconfirmed) | unknown | 30% | 60% | policy-search summary |

Operational metadata:

- input tokens: **3,105**
- output tokens: **4,881**
- latency: **51,652 ms**
- estimated API cost: **$0.0550**
- invalid evidence IDs: **0**

A detailed record is in [`experiments/2026-09-17-sonnet-baseline-smoke.md`](experiments/2026-09-17-sonnet-baseline-smoke.md).

### Correct interpretation

This run proves that:

- the local credential/config path works;
- the Anthropic request path works;
- structured output validates;
- evidence IDs round-trip correctly;
- run artifacts/metadata are persisted;
- the one-shot baseline can produce a plausible modernization ranking from sparse evidence.

It **does not** prove that:

- quote automation is truly Northstar’s highest-value opportunity;
- the $15K / $9.5K / $8K estimates are correct;
- Sonnet is stable across variants/runs;
- the baseline has been frozen;
- myAI beats the baseline;
- the startup thesis is validated.

The model lacks enough ground-truth cost/impact data to make those ROI values authoritative. They are model estimates, not labels.

---

## 10. Baseline model strategy

Do not use only Sonnet and then claim victory over “frontier models.”

Current planned roles, dated 2026-09-17:

- **Claude Sonnet 5** — development/reference baseline; fast and cheap enough for smoke tests.
- **Claude Opus 5** — **primary strong baseline** for the official benchmark. This is the control the structured system should materially beat.
- **Claude Fable 5.1** — **frontier ceiling / stress test**. Use it to test whether additional raw frontier-model capability already solves most of the task. It need not be the only official baseline.

Why use both Opus and Fable:

- Opus represents a very strong commercially plausible “just give the model all the context” alternative.
- Fable provides a capability ceiling. If Fable already solves the benchmark nearly perfectly, that is important evidence about where the project’s moat can or cannot exist.
- If myAI materially beats Opus and approaches Fable at lower cost, that can still be interesting.
- If myAI beats Fable on the task distribution, that is a much stronger technical result.

**Do not run the official Opus/Fable suite yet.** First freeze the evaluator and private answer key so later model outputs cannot bias how “correct” is defined.

Also add/record model reasoning/effort configuration explicitly before the frozen benchmark. The harness should not rely on an implicit provider default if the result is supposed to be reproducible months later.

---

## 11. Immediate next milestone: benchmark/evaluator freeze

This is the most important continuation instruction.

**Do not implement the Company Model/opportunity engine next. Do not collect a large set of Opus/Fable outputs next. Build the benchmark/evaluator first.**

Status: the public framework in §11.1 is **implemented** (§5, M1.5). The private pack in §11.2 and the randomized cases in §11.3 are **not yet authored**, and that is the current step.

The reason is experimental contamination: if we look at many frontier-model answers before defining the expected outcomes, it becomes easy to unconsciously shape the evaluator around what the models already said.

### 11.1 Public benchmark code to implement

The public repository may safely contain generic schemas and scoring code, for example:

- benchmark case ID / fixture variant ID;
- observable input manifest;
- opportunity category identifiers;
- evaluator interfaces;
- rank metrics;
- evidence-fidelity checks;
- policy/safety scoring;
- ROI-range scoring logic;
- calibration metrics;
- loader interface for an external/private answer pack;
- benchmark report aggregation.

Do not encode the actual Northstar hidden answers in those public files.

### 11.2 Private Northstar ground truth to create

Create a private pack outside normal runtime/coding-agent visibility, either:

- `benchmarks/private/` locally (already git-ignored), or
- a separate private repository / secure artifact store.

The private pack should contain, per benchmark case:

- hidden true opportunity classes;
- expected rank/order or value bands where determinable;
- hidden labor/cycle-time/cost assumptions;
- known decoys;
- policy constraints and prohibited autonomous actions;
- acceptable intervention classes;
- ambiguous/insufficient-evidence labels where no precise conclusion is justified;
- adversarial/contradictory evidence cases;
- hidden randomized seeds/parameters.

### 11.3 Randomized benchmark cases

Do not measure quality only by calling the identical eight-record Northstar prompt 20 times. That mostly measures model stochasticity.

Create a family of controlled variants where, for example:

- quote automation is genuinely highest-value in some cases;
- support triage is highest-value in others;
- finance reporting is a clear but smaller win;
- a tempting opportunity is actually a low-value decoy;
- available evidence is insufficient to justify a numeric ROI;
- policies make an otherwise attractive intervention unsafe;
- evidence conflicts and confidence should decrease;
- one workflow changes volume/cost enough to alter the ranking.

The system should not be told which variant it is expected to prefer; the evaluator knows.

### 11.4 Initial scorecard

At minimum track:

- top-1 opportunity correctness;
- top-3 recall of true high-value opportunities;
- ranking correlation with hidden value/order;
- evidence citation validity;
- factual/evidence support rate;
- unsupported ROI/claim rate;
- ROI calibration error or range coverage;
- policy-risk detection;
- critical policy violations;
- confidence calibration;
- run-to-run stability;
- latency;
- token usage;
- estimated cost.

Later, intervention stages add deterministic functional acceptance, regression, and business-proxy metrics.

---

## 12. Exact next implementation sequence

A new session should continue in this order unless new evidence materially changes the plan.

### Step 1 — Confirm repository/local health

```bash
cd ~/Projects/myAI
git switch main
git pull --ff-only origin main
source .venv/bin/activate
pip install -e '.[dev]'
ruff check .
mypy
pytest
```

Verify credentials without printing the secret:

```bash
grep -q '^ANTHROPIC_API_KEY=.\+' .env && echo "Anthropic key is configured"
```

If the key is multi-workspace scoped, also verify `ANTHROPIC_WORKSPACE_ID` is present.

### Step 2 — Implement M1.5 public benchmark framework — **DONE (2026-09-17)**

Delivered: typed case/answer/pack schemas, private-pack loader contract, rank/evidence/policy/ROI scoring, report aggregation, deterministic tests on a toy pack, and no real hidden answers committed. See §5 (M1.5) and [`adr/0002-benchmark-evaluator-framework.md`](adr/0002-benchmark-evaluator-framework.md).

**Known seam for the next session.** `build_baseline_request()` takes a `CompanyFixture` (a directory of `company.json` + `evidence.json`), while a `BenchmarkCase` carries company and evidence inline. Nothing yet runs a benchmark case through a model. Step 5 needs a small bridge — either a `CompanyFixture`-compatible view over a `BenchmarkCase`, or a `build_baseline_request` overload taking company+evidence directly. Prefer the latter; it keeps the prompt builder honest about what it actually consumes. **Do not change the baseline prompt text while doing this** — the prompt version is part of the frozen control, and `baseline_input_hash` must keep matching the recorded smoke run for the unchanged Northstar input.

### Step 3 — Author and freeze private Northstar benchmark pack — **DONE (2026-09-18)**

**Frozen:** pack `northstar-v1`, hash `a4174c2c0d58783bf47abf329ae959ced89d343e5b39d1047529b261f013ad32` (see [`experiments/2026-09-18-benchmark-freeze.md`](experiments/2026-09-18-benchmark-freeze.md)). The founder authored the pack privately via `myai benchmark-generate`; only the version and hash were shared into the build session.

Create the real holdout cases locally/private. Decide the hidden outcome/value/policy truth **before** running large frontier-model batches.

**A parameterized generator now exists** (`src/myai/benchmark/generator.py`, `myai benchmark-generate`): the human author supplies a private params file (seed, loaded labor rates, automatable fractions, band width, floor) and the generator derives observable evidence and hidden truth from the same drawn numbers, recomputed from displayed values. This was chosen over hand-authoring 20 variants because it guarantees evidence/answer consistency and keeps the coding agent blind to specific case answers (the agent knows the formulas — which are the task definition — but not the seed or draws). The format for manual authoring also remains documented in [`../benchmarks/README.md`](../benchmarks/README.md#authoring-a-private-pack).

The human author's remaining duties: set a private seed, approve the business constants in the params file, spot-check several cases in the generated `manifest.json` for realism, then:

```bash
myai benchmark-validate
```

This validates completeness, prints the `pack_hash`, and refuses to run if the pack is tracked by Git. Record that hash — it is the frozen target every later report is stamped against.

Author roughly 20 **distinct** variants covering the case types listed in §11.3: quote-dominant, triage-dominant, finance-as-smaller-win, attractive decoy, unsizeable opportunity, policy-unsafe intervention, contradictory evidence, and volume shifts that change the correct ranking. Write the `notes` field on each answer explaining *why* the hidden ranking is true; a future session cannot re-derive that reasoning from the numbers alone.

One practical warning: the observable evidence for each variant has to be authored too, not just the answers. A variant where triage is genuinely highest-value needs evidence that actually supports that conclusion, or the benchmark measures guessing rather than reasoning.

### Step 4 — Harden/freeze baseline configuration — **DONE (2026-09-18)**

The benchmark runner exists (`src/myai/benchmark/runner.py`, `myai benchmark-run`): it reuses the frozen baseline-v0.1 prompt via `build_context_request` (fixture input hash verified unchanged against the recorded smoke run, `89f65eef…`), persists immutable per-case artifacts under `runs/benchmark_*/`, scores against the private pack, excludes failed cases from reports loudly, and refuses to run when `--expect-hash` does not match the loaded pack.

Reasoning configuration is now explicit: every request sends `thinking={"type": "adaptive"}` and `output_config={"effort": ...}` (default `high`, the documented API default — behaviorally identical to the smoke run's implicit default, but now recorded in `request.json` and the suite record). Model IDs were verified live against the Models API on 2026-09-18: `claude-sonnet-5`, `claude-opus-5`, and `claude-fable-5-1` all exist; Fable 5.1 pricing ($10/$50 per MTok, verified against the live models-overview doc) was added to the provider cost table. Sonnet 5 pricing ($2/$10) was re-verified as current.

Before official runs:

- make reasoning/effort level explicit in request configuration and run metadata where supported;
- keep baseline prompt version frozen;
- keep exact observable input hash;
- verify model IDs;
- ensure costs/tokens/latency are recorded;
- ensure failed runs cannot silently count as valid benchmark cases.

### Step 5 — Run official frontier baselines — **DONE (2026-09-18)**

All three suites complete, 20/20 each. Headline: **Opus 5 (primary control) scores 95% top-1 / 100% top-3 / rho 0.975 — discovery and ranking are near-ceiling for one-shot prompting on this pack.** Grounding and policy safety are commodity (zero fabrications/violations for all models). The only open axis is value: unsupported ROI (Sonnet 11% / Opus 26% / Fable 5%), ROI calibration error (0.180 / 0.568 / 0.329), band coverage (88% / 73% / 78%). Full table, decisiveness caveats, and interpretation: [`experiments/2026-09-18-official-baseline-report.md`](experiments/2026-09-18-official-baseline-report.md).

**Sequencing consequence — read before building anything:** the structured Company Model can no longer be justified by discovery improvement (the charter's falsification rule applies). Before implementing Step 6, run a **baseline-v0.2 hardened-prompt experiment**: same one-shot control, prompt extended with an explicit abstention policy (no `annual_value_usd` unless volume, time, and rate are all evidence-supported) and assumption disclosure. If prompt-level discipline closes the value gap too, the kill gate (Step 7) applies to the architecture thesis on this benchmark and the correct responses are those listed there (narrow the wedge, keep only measurably-helpful pieces, or redirect the thesis toward the intervention/measurement loop the benchmark does not yet test). Keep baseline-v0.1 frozen; v0.2 is a separate tracked prompt version. Also worth buying before big conclusions: a `--repeat 3` stability measurement on selected cases (top-1 differences of 2/20 are within single-run noise).

### Step 5 (original plan) — Run official frontier baselines

Suggested initial suite after the evaluator is frozen:

- Sonnet 5 on the benchmark family as a development/reference baseline;
- Opus 5 as the primary strong control;
- Fable 5.1 as the frontier ceiling/stress test.

Start around **20 distinct benchmark cases**, not 20 duplicates. Repeat selected ambiguous cases if variance needs measurement.

Produce a frozen baseline report before implementing the structured intelligence layer.

### Step 6 — Implement the first structured myAI system

Only after baseline freeze:

1. infer a typed Company/Workflow Model from the same observable evidence;
2. maintain provenance back to evidence IDs;
3. generate candidate opportunities;
4. run a skeptic/evidence challenge;
5. estimate value/feasibility/risk with explicit assumptions;
6. rank opportunities;
7. score against the same private evaluator.

Prefer a single explicit typed pipeline/state machine before adding agent frameworks or many autonomous personas.

### Step 7 — Apply the kill gate

If the structured system does not materially outperform the strong one-shot control, do not keep adding complexity.

Potential responses:

- simplify to a narrower high-value wedge;
- retain only the pieces that measurably help (e.g. provenance or calibration);
- test a services/assessment product if discovery is useful but implementation stays bespoke;
- stop the horizontal-platform thesis if no repeatable advantage appears.

### Step 8 — Only after discovery/ranking wins: build intervention/evaluation

Pick one bounded intervention class, build it in a synthetic sandbox, and evaluate before/after behavior deterministically where possible.

Do not jump to production connectors, deployment controls, or a SaaS dashboard first.

---

## 13. Benchmark bars currently envisioned

These are working gates, not sacred constants:

- top-3 discovery hit rate around >=80% across randomized cases;
- evidence fidelity around >=95% on sampled claims;
- zero fabricated evidence IDs;
- materially better hidden-value/rank correlation than the one-shot baseline;
- later intervention acceptance >=90% on deterministic cases;
- zero critical policy violations;
- end-to-end relative improvement around >=20% over the strong one-shot baseline **or** a clearly valuable capability the baseline cannot perform;
- second-company generalization through config/data rather than core-code rewrites.

The crucial rule is comparative: **System C must earn its added complexity over Baseline A/B.**

---

## 13.5 Post-kill-gate strategic assessment (2026-09-18)

The services option from Step 7 was researched and scored against the founder's commit criteria in [`research/services-pivot-assessment.md`](research/services-pivot-assessment.md). Summary: real demand (AI-naive mid-market buyers confirmed), no structural white space (frontier labs entered implementation services at $4B/$1.5B scale in May 2026; bottom tier flooded), income-business economics (~5–10% probability of a $5M+ outcome as pure services). Recommended shape if pursued: time-boxed services-as-discovery with a measured-outcome positioning, tracking percent-effort-reused per engagement as the productization signal.

## 14. Open design questions

These remain intentionally unresolved until the benchmark generates evidence:

- How much company context is minimally sufficient?
- Does an explicit Company Model materially outperform high-quality long-context retrieval?
- How accurately can ROI be calibrated from incomplete enterprise evidence?
- What is the first intervention class with objective, deterministic acceptance tests?
- How much human review belongs in discovery vs implementation?
- When, if ever, does proprietary data justify fine-tuning/distillation?
- Can a small team serve the mid-market with better margins/time-to-value than FDE-heavy competitors?
- Which pieces of the eventual “Company Graph” deserve durable persistence vs recomputation?

Do not prematurely settle these with taste or architecture preference. Use benchmark evidence.

---

## 15. Things deliberately deferred

Do not treat the following as missing chores. They are deferred on purpose:

- Postgres / pgvector;
- Neo4j or other graph database;
- FastAPI service layer;
- Next.js dashboard;
- OpenTelemetry deployment-grade observability;
- Temporal/Celery/LangGraph orchestration;
- production enterprise connectors;
- real customer data;
- autonomous production writes;
- proprietary-model training;
- broad intervention-builder platform.

The intelligence/evaluation question is the risk. Infrastructure is not the current risk.

---

## 16. Security, secrets, and public-repo rules

Local `.env` may contain:

```text
ANTHROPIC_API_KEY=...
ANTHROPIC_WORKSPACE_ID=...   # only if needed
```

Never print or commit the key. `.env` is ignored by Git.

`runs/` is local and ignored because raw experiment artifacts may be noisy, numerous, or sensitive later.

`benchmarks/private/` is ignored because hidden answer keys must not be visible to the runtime or ordinary coding agents. A “hidden” folder committed to a public repository is not hidden.

Do not add a LICENSE without an explicit IP/open-source decision. The project may become proprietary startup work.

---

## 17. How to interpret progress

Current status is:

- **Market need:** supported by desk research.
- **Competitive whitespace:** plausible but contested; category active and early.
- **M0 engineering foundation:** complete.
- **M1 live baseline plumbing:** complete.
- **First Sonnet smoke experiment:** complete and technically successful.
- **M1.5 public benchmark/evaluator framework:** complete.
- **Private Northstar answer key:** authored and frozen 2026-09-18 (`northstar-v1`, `a4174c2c…`).
- **Benchmark runner:** implemented and exercised (disk-full-resilient, offline rescore verified).
- **Official trusted baseline:** **established 2026-09-18** — Sonnet/Opus/Fable, 20 cases each, frozen report in `experiments/2026-09-18-official-baseline-report.md`. Opus one-shot near-ceiling on discovery; value calibration is the only open axis.
- **Baseline-v0.2 hardened-prompt control:** executed 2026-09-18. **Unsupported ROI 26% → 0%, calibration error 0.568 → 0.192, Brier 0.187 (best of all runs).** One prompt paragraph closed the last reasoning gap. **The Step 7 kill gate applies to the structured reasoning thesis: do not build the Company Model / opportunity engine for provided-evidence reasoning.** See [`experiments/2026-09-18-baseline-v02-kill-gate.md`](experiments/2026-09-18-baseline-v02-kill-gate.md) for the verdict and what survives (evidence acquisition, intervention execution, outcome measurement, and outcome-data-driven calibration remain untested and open).
- **Company Model / structured opportunity engine:** not yet built.
- **Intervention sandbox:** not yet built.
- **Evidence that myAI beats frontier one-shot reasoning:** **none yet**.

That last point matters. The project has earned the right to run the experiment; it has not yet proven the thesis.

---

## 18. Suggested read order for a new LLM session

A new session should read:

1. this file;
2. `POC_CHARTER.md`;
3. `docs/founder-one-pager.md`;
4. `docs/research/market-landscape.md`;
5. `benchmarks/README.md`;
6. `docs/adr/0001-foundational-architecture.md`;
7. `src/myai/domain.py`;
8. `src/myai/baseline.py`;
9. `src/myai/model_gateway.py`;
10. `src/myai/providers/anthropic.py`;
11. `src/myai/run_store.py`;
12. `src/myai/cli.py`;
13. Northstar fixture JSON;
14. `docs/adr/0002-benchmark-evaluator-framework.md`;
15. `src/myai/benchmark/schema.py` and `src/myai/benchmark/scoring.py`.

After that, the correct default action is **author and freeze the private Northstar benchmark pack** (§12 Step 3), not more generic research, UI work, or agent orchestration. The public framework that consumes the pack already exists.

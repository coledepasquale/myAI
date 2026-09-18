# 2026-09-18 — Northstar benchmark pack frozen

The private Northstar benchmark pack was authored and frozen on 2026-09-18.

- **Pack version:** `northstar-v1`
- **Pack hash:** `a4174c2c0d58783bf47abf329ae959ced89d343e5b39d1047529b261f013ad32`
- **Scorer version at freeze:** `scorer-v0.2`
- **Cases:** 20, cycling the eight archetypes (quote-dominant, triage-dominant, finance-dominant, near-tie, decoy-prominent, insufficient-evidence, policy-trap, contradictory-evidence)
- **Authoring method:** `myai benchmark-generate` from a private parameter file (seed and generated pack held privately by the founder; only version and hash were shared back into the session that builds the system)

## Provenance of the parameters

- Loaded labor rates were grounded in BLS May-2025 OEWS medians x1.43 benefits load (BLS ECEC: benefits ~30% of total compensation), with a ~10% regional/small-firm discount.
- Automatable fractions were author-judged on 2026-09-18: quote preparation 0.8, support triage 0.85, finance reporting 0.8, policy self-service 0.85. The policy self-service figure is deliberately above typical measured industry deflection (40–60%); it defines the benchmark world's physics for a well-engineered system and applies equally to baseline and structured runs.
- ROI band width ±35%; high-value floor $12,000/yr; 20 cases.

## What this hash means

Every future benchmark report must carry this pack hash to count as a result
against the frozen target. A report with a different hash was measured against a
different target and is not comparable. The pack was frozen **before** any
frontier-model outputs were collected against it, so the evaluator cannot have
been shaped by what models happen to say.

## Verification

```bash
myai benchmark-validate            # re-prints the hash from the local private pack
myai benchmark-run --expect-hash a4174c2c0d58783bf47abf329ae959ced89d343e5b39d1047529b261f013ad32 --model claude-sonnet-5
```

`benchmark-run --expect-hash` refuses to execute paid calls if the local pack
does not match the frozen target.

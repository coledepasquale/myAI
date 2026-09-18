# Services pivot assessment — "diagnose + bespoke build" for AI-naive mid-market

**Date:** 2026-09-18. Follows the benchmark kill gate (see
`../experiments/2026-09-18-baseline-v02-kill-gate.md`). Evaluates the charter
Step 7 option "test a services/assessment product": enter AI-naive mid-market
companies (20–500 employees), diagnose AI opportunities with a frontier model,
build the chosen intervention bespoke.

## Market facts (researched 2026-09-18)

- US AI consulting projected >$15B in 2026; AI-strategy engagements grew 89%
  YoY in 2025. Mid-market engagements price $35K–$200K over 3–6 months;
  solo consultants bill $150–$350/hr with $2–10K/mo retainers.
- Demand side is real and matches the "don't know what they don't know"
  hypothesis: only ~27% of small businesses feel confident adopting AI, yet
  ~68% of US small businesses now use AI regularly, and 78% of successful
  deployments involved external partners.
- Failure rates create a "second-attempt buyer" segment: ~42% of companies
  abandoned most AI initiatives in 2025 (up from 17% in 2024); Gartner projects
  >40% of agentic projects canceled by 2027.
- Supply is crowded at every tier: Big 4 / strategy firms (enterprise),
  mid-market consultancies, AI-native boutiques, and tens of thousands of
  low-quality "AI automation agencies" at the bottom.
- **The frontier labs entered the market directly in May 2026:** OpenAI
  launched the Deployment Company (~$4B initial investment, forward-deployed
  engineers, acquiring firms — bought Tomoro, 150 people); Anthropic launched
  "Ode" (~$1.5B JV with Blackstone, Hellman & Friedman, Goldman). Accenture
  bought Faculty (~£50M run-rate) at ~$1B ≈ 15x revenue, plus Halfspace and
  Keepler.

## Verdict against the founder's commit criteria

| Criterion | Verdict |
|---|---|
| Significant revenue | **Pass as income**: $300K–$1M/yr solo+1 within 12–24mo is realistic at market rates |
| Real white space | **Fail.** Not "dominated" (services markets never are), but contested at every tier, including by the model labs themselves. The quality gap at 20–500 employees is a reputation market, not structural white space |
| Solo+1 buildable | Delivery yes; the **sales motion is full-time founder work** (sell–deliver–sell treadmill; mid-market trust cycles). Not compatible with side-project pace |
| $5M+ liquidity in 12–48mo | **Fail (~5–10%).** Small services firms exit at ~1–3x revenue / 3–5x EBITDA; reaching a $2–5M-revenue firm means 10–20 headcount, no longer solo+1. Faculty's 15x was a decade-old, 300-person, £50M firm |
| Career-defining company | **Fail** as an endpoint; possible as a wedge (below) |
| Interesting + tangible | Pass |
| Buyer not AI-savvy | **Strong pass** — the founder's hypothesis about this buyer is correct and data-supported |
| No TOS/regulatory traps | Pass (note: employer moonlighting/COI review required before first paid engagement) |

**Net: viable income business, not the target company.** "Is the space
dominated?" — no, and it never will be, because services markets fragment
rather than consolidate; that same property caps the outcome.

## The bespoke-build question

Claim under test: "every client's quote-drafter must be bespoke because every
stack is unique." Partially true, and the distinction determines everything:

- Genuinely bespoke per client: integration glue, auth, data mapping, deploy.
- Reusable across clients: discovery playbook, evidence-extraction prompts,
  eval/measurement harness (already built in this repo), guardrail/approval
  patterns, agent scaffolds, ROI-tracking instrumentation.

If reuse across the first three clients trends toward 60–80% of effort, a
product is hiding inside the practice. If it stays near zero, this is a body
shop permanently. **This is an empirical question — track percent-effort-reused
per engagement from client #1.**

## Surviving strategic shape (if pursued at all)

Services-as-discovery, explicitly time-boxed: 3–5 paying mid-market clients in
12–18 months, positioned on the two data-supported wedges — (a) second-attempt
buyers burned by a failed AI initiative, (b) measured-outcome accountability
("we instrument before/after; you pay against measured savings") — with the
repo's evaluation harness as differentiating IP. Each engagement doubles as
customer-funded R&D hunting for the reusable 60–80% and accumulating the
predicted-vs-actual ROI dataset that real calibration requires. Convert to
product only if the reuse ratio and outcome data justify it; otherwise treat
as income and stop deliberately.

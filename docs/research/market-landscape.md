# AI modernization market landscape — research snapshot

**Snapshot date:** September 2026

This document captures the market research that motivated the myAI POC. It is intentionally written as a working founder research note rather than as a claim that the market is static.

## Executive conclusion

The horizontal AI-transformation market is **occupied but not mature**.

There are meaningful incumbents and one especially important horizontal competitor, but many of the closest AI-native companies are extremely young and very small. The category still looks like an early land grab rather than a market with an established architectural standard or dominant winner.

That supports a measured technical experiment. It does **not** support building a generic "AI audit" or "AI consulting report" product.

## Market pain

Public 2026 research supports several parts of the thesis:

- AI adoption among small and midsize employers is broad, but deep integration remains limited.
- Businesses report difficulty adapting AI to their actual needs, choosing appropriate tools, implementing them, training employees, and proving ROI.
- Productivity gains are common, but many firms still report relatively modest improvements, leaving room for deeper workflow redesign.
- Larger consultancies and enterprise software vendors are investing heavily in AI transformation, which validates willingness to spend.

Representative sources:

- Federal Reserve Small Business Credit Survey, 2026 Report on Employer Firms: https://www.fedsmallbusiness.org/2026-report-on-employer-firms
- Upwork, State of AI in SMBs: https://www.upwork.com/resources/state-of-ai-in-smbs
- McKinsey, State of AI: https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai
- Accenture annual / integrated reporting: https://www.accenture.com/us-en/about/company/integrated-reporting-financial

## Closest horizontal competitors

### Within (formerly Klarity)

https://www.within.ai/

The strongest direct horizontal threat identified so far. Within describes a system that learns how a company works, builds a living company/process representation, finds opportunities for AI agents, and supports transformation around humans and agents.

Important maturity nuance: Klarity existed for years, but the broad **Within / Company Brain / AI transformation** positioning is recent (2026). This is therefore not equivalent to a nine-year head start on the exact current product thesis.

Why it matters to us: Within validates the company-model / organizational-context layer and is the competitor we should study most carefully as our architecture evolves.

### Workhelix

https://www.workhelix.com/

Focuses on identifying where AI creates value and measuring AI usage / ROI. It has raised meaningful venture funding and has enterprise customers.

Why it matters: validates that opportunity identification and ROI measurement are valuable, but its visible emphasis is less about autonomously implementing and evaluating interventions end-to-end.

### Foaster

https://www.ycombinator.com/companies/foaster

Very young, small AI-native team. Positions itself around AI-led discovery of how employees work, mapping workflows, bottlenecks, and AI opportunities, then combining that with transformation support.

Why it matters: generic "AI interviews employees and produces a transformation roadmap" is already being built. That cannot be our core novelty.

### Ontora

https://www.ycombinator.com/companies/ontora

Another very young company focused on the organizational discovery layer for AI transformation: understanding how work happens before deciding what should be automated.

Why it matters: reinforces that discovery/context is a recognized bottleneck but also a crowded wedge.

### Marker

https://www.ycombinator.com/companies/marker

Positions around understanding workflows, ranking AI opportunities by business impact, and then building/deploying agents.

Why it matters: close to the discover → prioritize → implement loop. We should differentiate through repeatable evidence-grounded evaluation and progressively lower human/FDE dependence.

### Terminal Use / Autostep / Sona8 / Trace

These companies attack adjacent pieces such as workflow observation, process mapping, context capture, transformation, and agent implementation. Many are teams of only a handful of people.

Implication: the race is active now; we are not entering behind a mature generation of 500-person AI-native competitors.

## Mature adjacent incumbents

### Celonis

https://www.celonis.com/

Mature process-intelligence platform with large enterprise distribution and extensive process-data integration. Increasingly positions process intelligence as a context layer for enterprise AI and agents.

Threat: existing data/integration footprint and enterprise relationships.

Opportunity: Celonis is optimized for large-enterprise process intelligence, not necessarily a lightweight autonomous modernization product for smaller organizations.

### UiPath

https://www.uipath.com/

Large automation/RPA incumbent with task mining, process discovery, and agentic automation capabilities.

Threat: deep enterprise workflow footprint, integrations, governance, and existing budgets.

Opportunity: RPA heritage and enterprise deployment model differ materially from a small-team, model-native closed-loop modernization system.

### ServiceNow / Salesforce / Microsoft / Palantir

All are adding agentic capabilities inside their ecosystems.

Threat: they own important systems of record, customer relationships, and distribution.

Opportunity: a horizontal modernization layer may live **across** systems of record rather than replacing them.

## Services competitors

### Accenture and other global consultancies

Consultancies are investing heavily in forward-deployed AI transformation capability, workflow redesign, and implementation.

This is strong market validation: major organizations are willing to spend heavily to determine where AI matters and then implement it.

However, the delivery model is labor-heavy. A small AI-native company could potentially serve organizations that cannot justify large consulting engagements or could deliver similar discovery/implementation loops with radically lower human effort.

## What appears commoditized or rapidly commoditizing

### Generic AI opportunity assessments

Many consultancies and agencies now offer AI audits, maturity assessments, or opportunity maps cheaply or even for free as the top of a sales funnel.

Conclusion: **the assessment/report itself is not enough of a product.**

### "Interview employees and map workflows"

Multiple startups now use AI interviews or activity observation to discover workflows.

Conclusion: this can be a component, but it should not be our entire moat.

### Agent builders

Foundation-model vendors, automation companies, and startups all make it increasingly easy to build agents.

Conclusion: "we can build an agent" is not a durable differentiator.

## The whitespace we want to test

Our working differentiation is the **closed modernization loop**:

1. ingest evidence about an organization;
2. form an explicit, inspectable company/workflow model;
3. generate and rank opportunities with evidence and assumptions;
4. challenge recommendations and calibrate uncertainty;
5. build a bounded candidate intervention;
6. evaluate it against hidden correctness, policy, cost, and business-proxy tests;
7. require approval where appropriate;
8. measure outcomes and repeat.

The key question is not whether every step is individually novel. Most are not.

The key question is whether integrating these steps into a product creates **materially better decisions and interventions with materially less human consulting** than existing approaches.

## Why a small team can plausibly compete

Most of the newest direct competitors are tiny. Frontier models, coding agents, browser/computer-use capabilities, embeddings, tool protocols, and cloud infrastructure dramatically reduce the amount of custom software required to test the concept.

A small excellent team can likely reproduce the visible feature surface of many early entrants quickly.

But this cuts both ways: competitors have access to the same models. Therefore **engineering velocity alone is not a moat**.

Potential durable advantages would need to emerge from some combination of:

- a superior company/workflow representation;
- evidence provenance and calibrated decision quality;
- a strong evaluation/sandbox layer;
- proprietary transformation trajectories and outcomes;
- integrations and accumulated organizational context;
- faster/safer implementation loops;
- distribution and customer trust.

## Horizontal vs vertical strategy

Vertical markets such as construction, manufacturing, logistics, accounting, legal, insurance, home services, and property management all contain valuable repetitive workflows. They also increasingly contain specialized AI startups.

Verticalization improves distribution and repeatability, but it does not automatically create greenfield space.

The preferred current strategy is therefore:

> **Horizontal product ambition; initially narrow customer archetype.**

For example, begin with organizations large enough to have meaningful workflow/process spend but small enough not to possess sophisticated internal AI engineering teams. The initial customer cohort may be narrow without hard-coding an industry into the core platform.

## Competitive design guidance for the POC

Competitor activity suggests several design choices:

- Company/process context should be first-class rather than dumped into an unstructured prompt.
- Evidence provenance matters because enterprise recommendations need to be auditable.
- Opportunity ranking must express business value, feasibility, cost, confidence, and assumptions.
- Recommendations alone are weak; implementation is increasingly expected.
- Implementation alone is becoming commodity; objective evaluation is strategically important.
- Human approvals and constraints should be explicit rather than bolted on later.
- Model/provider independence is prudent because base-model capability is moving rapidly.

## Critical falsification question

The most important technical/business benchmark is:

> **Does the structured myAI system materially outperform frontier model + all available company context + an excellent one-shot prompt?**

If not, then much of the proposed architecture is ornamental and should be simplified.

## Current founder decision

As of September 2026:

- **Market need:** strongly validated.
- **Willingness to spend on AI transformation:** validated.
- **Horizontal competitive category:** active but not settled.
- **Generic AI audit:** poor standalone wedge.
- **Closed-loop modernization:** promising but unproven.
- **Small-team entry:** plausible.
- **Recommendation:** build a falsifiable 4–6 week POC, not a production company/platform.

## Research caveat

Competitor funding, team size, positioning, and customer counts can change quickly. Before making major fundraising, hiring, or go-to-market decisions, refresh this research rather than treating this document as static truth.

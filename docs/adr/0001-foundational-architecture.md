# ADR 0001 — Foundational architecture

Status: accepted for POC v0.1

## Context

The project is testing whether explicit company modeling, evidence provenance, and closed-loop evaluation create materially better modernization decisions than a strong frontier-model baseline. The main risk is overbuilding an agent platform before establishing that architectural scaffolding adds value.

## Decision

- Use Python 3.12 for the research/control plane.
- Use Pydantic models at domain boundaries.
- Keep model providers behind a `StructuredModel` protocol.
- Treat evidence IDs, assumptions, and confidence as first-class data.
- Use a controlled synthetic-company fixture before integrating real customer systems.
- Build a reproducible one-shot baseline before multi-agent orchestration.
- Use a CLI and benchmark reports before investing in a product UI.
- Do not train proprietary models until a repeatable capability gap is measured.
- Keep hidden benchmark truth outside runtime inputs.

## Why

These choices maximize experimental clarity, provider portability, and falsifiability while minimizing infrastructure that does not test the startup thesis.

## Revisit when

- real customer integrations require durable storage or event processing;
- benchmark volume makes the in-memory evidence store inadequate;
- model traces justify specialized fine-tuning or distillation;
- the intervention sandbox requires isolated execution infrastructure;
- a validated user workflow justifies a web product surface.

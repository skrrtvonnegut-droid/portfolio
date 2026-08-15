---
id: portfolio.project-card.prompt-library
title: Prompt Library
summary: A versioned registry that treats prompts, skills, macros, and authoring templates as inspectable software-like artifacts with stable identity, routing metadata, validation, and explicit privacy boundaries.
artifact_type: project-card
domains:
  - ai-llm
  - automation
  - documentation
status: active
classification: professional-portfolio
source_disclosure: Derived only from the intentionally public prompt-library repository; private registry overlays, personal defaults, and private source material are not included.
skills:
  - AI workflow architecture
  - Schema design
  - Technical writing
  - Governance
  - CI validation
created: 2026-08-15
updated: 2026-08-15
---

# Prompt Library

> **Portfolio note:** This page summarizes the public system and its design decisions. The canonical prompt, skill, macro, and template bodies remain in the [Prompt Library repository](https://github.com/skrrtvonnegut-droid/prompt-library).

## Why it exists

Prompts are often treated as disposable text: useful once, copied into another chat, gradually modified, and eventually impossible to distinguish from several near-duplicates. That model works poorly when an instruction becomes part of repeatable technical or creative work.

Prompt Library treats reusable AI instructions more like maintained artifacts. Human-readable Markdown contains the canonical body, while a machine-readable catalog supplies stable identity, aliases, domain, classification, lifecycle, and routing metadata.

The goal is not to turn every sentence into infrastructure. It is to give recurring capabilities enough structure that they can be found, inspected, versioned, validated, and improved without losing their meaning.

## Artifact model

The registry distinguishes four public artifact types:

- **Prompts** — reusable instruction sets that operate on supplied inputs.
- **Skills** — deeper routed capabilities with procedure, dependencies, guardrails, failure handling, and an output contract.
- **Macros** — compact named commands that expand into a prompt or skill invocation.
- **Templates** — scaffolds for creating new registry artifacts consistently.

The distinction is deliberately functional rather than hierarchical. A small macro can be exactly the right abstraction; a skill earns its additional ceremony only when the work actually requires routing, tools, state, dependencies, or explicit failure behavior.

## Stable identity and runtime resolution

`catalog.yml` gives each artifact a durable ID and registered aliases. A compatible assistant can resolve an invocation in an explicit order:

1. exact stable ID;
2. registered alias;
3. artifact name;
4. intent using summary and domain;
5. retrieval of the canonical Markdown body.

This makes the repository the source of truth rather than relying on whatever version of a prompt happens to be present in a conversation context.

## Design choices

### One canonical body

Catalog entries and macros point to canonical Markdown rather than duplicating full instruction bodies. This reduces drift and keeps editing human-legible.

### Stable identity over path

A filename may eventually move; the stable artifact ID is intended to remain meaningful. That makes references more durable and gives lifecycle operations such as aliasing or supersession something firmer than a directory path.

### Search before creation

The authoring workflow emphasizes deduplication before adding another artifact. The preferred outcome may be improving an existing prompt, relating a new skill, or adding an alias rather than multiplying almost-equivalent instructions.

### Classification as part of the registry

The public repository permits Public and intentionally sanitized Professional Portfolio artifacts. Personal Private, Employer Confidential, and Secrets are outside the public membrane. A private deployment can extend the public catalog without copying private material into the public repository.

### Validation before trust

Catalog integrity is checked automatically. Registered IDs, aliases, paths, and classifications are therefore not merely documentation conventions; they are machine-checkable parts of the repository contract.

## Human and AI authorship

The project is itself AI-assisted work. AI can help structure artifacts, identify inconsistencies, and accelerate authoring, but stable identity, classification, publication decisions, and maintainer responsibility remain explicit human concerns. The registry is designed so a person can inspect the actual instructions instead of interacting with an opaque learned behavior.

That distinction matters because fluent generated text can look authoritative even when provenance, applicability, or uncertainty is weak. The system therefore favors visible assumptions and explicit failure handling over seamless-looking invention.

## Current maturity

The registry is active and versioned through normal Git workflows. Its public contract supports prompts, skills, macros, templates, validation, and routing metadata. It does not imply that every compatible AI host exposes identical tools, permissions, or runtime behavior; artifact execution still depends on the capabilities available to the assistant using the registry.

## What this demonstrates

- Designing reusable AI workflows as maintained artifacts rather than disposable chat text
- Combining human-readable Markdown with machine-readable registry metadata
- Stable identity, aliasing, lifecycle, classification, and deduplication design
- CI-backed schema and catalog validation
- Separating portable public capabilities from deployment-specific private overlays
- Treating AI assistance as something to govern and inspect rather than conceal

## Canonical repository

Browse the current catalog, schemas, skills, macros, templates, and validation tooling in [Prompt Library](https://github.com/skrrtvonnegut-droid/prompt-library).

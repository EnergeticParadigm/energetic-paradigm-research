# Experimental Proposal PoC (Public Version)

## Proof of Concept for Endogenous Structural Governance in Capability-First AI

Based on *Capability-First AI or Structural Constraint: Endogenous Governance Through the Energetic Paradigm*

### Purpose

This public proof-of-concept proposal translates the core claim of the paper into a small, reproducible experiment. The main question is whether governance built into generation conditions can reduce downstream governance burden, unstable candidate formation, and effective resource cost, while preserving comparable task success.

The public version is intentionally limited. It is meant to disclose the experimental direction and the mechanism class being tested, while withholding implementation-sensitive details, internal execution thresholds, and later-stage expansion logic.

### Central Research Question

In a controlled sequential decision environment, can a generation-time structural-governance regime achieve task success comparable to a reactive-governance baseline while producing fewer unstable paths, lower downstream governance burden, and more stable effective resource usage?

### Hypotheses

The public PoC tests the following hypotheses:

- H1: The structural-governance regime will achieve task success comparable to the reactive-governance baseline.
- H2: The structural-governance regime will produce fewer unstable candidate branches than the reactive-governance baseline.
- H3: The structural-governance regime will require fewer downstream governance interventions.
- H4: The structural-governance regime will have lower effective resource cost per successful task completion.
- H5: As branching complexity increases, governance burden will grow more slowly under structural governance than under the reactive-governance baseline.

### Experimental Strategy

The first public experiment uses a synthetic path-search environment rather than a natural-language benchmark. The purpose is to isolate the mechanism cleanly under controlled conditions.

All regimes operate on the same environment. The comparison is architectural rather than domain-specific. The relevant difference is when governance enters the process:

- one regime generates first and applies governance afterward;
- the other embeds governance into transition formation itself.

### Minimal Public Environment Description

The experiment uses a procedurally generated directed state-space environment with one start node, one goal node, and multiple candidate paths between them.

Each transition includes three conceptual attributes:

- task utility contribution,
- energetic cost,
- instability risk.

The environment is designed so that multiple paths can reach the goal, but not all successful paths are equally sustainable. Some paths are higher-cost, higher-instability, or more likely to require later repair.

### Public Regime Definitions

**Baseline 1: Capability-First, No Governance**

The agent expands paths using task-oriented criteria without structural control during generation.

**Baseline 2: Reactive Governance**

The agent first generates candidate paths. Governance checks occur afterward and may reject, repair, retry, or roll back candidates.

**Regime 3: Endogenous Structural Governance**

The agent applies structural admissibility during generation, so unstable or unsustainable transitions are suppressed before they become full candidate paths.

### Public Evaluation Metrics

The public PoC evaluates both performance and governance burden. The main metrics are:

- task success rate,
- governance intervention count,
- unstable branch frequency,
- effective resource cost per success,
- mean accepted path cost,
- governance-efficiency ratio,
- complexity slope under increasing branching conditions.

### Expected Result Pattern

If the architectural claim is correct, the capability-first no-governance baseline may sometimes perform well in easier settings, but it should produce the highest latent structural risk.

The reactive-governance baseline should achieve acceptable task success, but with visibly higher downstream governance burden.

The structural-governance regime should achieve similar or only slightly lower task success while producing fewer unstable branches, fewer downstream interventions, and lower effective resource cost. As task complexity increases, governance burden should rise more slowly under structural governance.

### Scope of This Public Version

This public version intentionally omits:

- implementation-sensitive scoring details,
- transition-gating thresholds and internal parameter choices,
- execution scripts and repository file map,
- source-code share links,
- internal runtime and output specifications,
- internal acceptance thresholds,
- post-PoC expansion roadmap.

### Concluding Statement

This proof of concept is intended to provide an initial empirical entry point for the architectural claim made in the underlying paper: governance can be moved from post-generation correction into generation conditions themselves.

The public release is designed to show the experiment’s purpose, structure, and evaluation logic while reserving internal implementation details for later release.

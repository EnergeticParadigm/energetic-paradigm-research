# Experimental Proposal - Public Redacted Version

## Validating the Energetic Paradigm through Temporal Path Experiments

Based on *From Representation to Path*

## Purpose

This public version presents the experiment's conceptual design without publishing the executable blueprint. The central claim remains visible: in systems with delayed burden and threshold effects, a model that explicitly tracks path variables such as load, delay, and risk should remain more stable over long horizons than a model that predicts only the next state.

## Central Research Question

In a system with accumulated load, delayed release, and threshold risk, can a path-aware model outperform a baseline next-state model in long-horizon stability, failure reduction, and earlier risk recognition?

## Public Hypotheses

- The EP-style model should show a lower trajectory failure rate than the baseline model.
- The EP-style model should exhibit lower long-horizon drift.
- The EP-style model should estimate risk earlier and more accurately.
- As horizon length or delay strength increases, the performance gap should widen.

## Public Experiment Outline

The experiment is framed as a synthetic delayed-load environment rather than a large real-world benchmark. This keeps the first-stage test focused on mechanism identification.

A baseline model learns next-state prediction only. An EP-style model learns next-state prediction together with path variables related to load, delay, and risk. Both models are intended to have broadly comparable capacity so that any difference comes from path supervision rather than simple size advantage.

This public version deliberately leaves out exact state equations, loss definitions, parameter settings, file structure, and execution details. Those items belong to the private implementation package rather than the public research-facing summary.

## Public Evaluation Dimensions

- Trajectory failure rate over rollout
- Long-horizon drift rather than only single-step fit
- Risk prediction quality, including whether risk rises before collapse
- Qualitative risk-over-time behavior as an interpretability check

## Expected Public Result Pattern

The baseline model may look adequate in short-span prediction, but it should be more vulnerable in closed-loop rollout because it does not explicitly account for accumulated burden and delayed damage. The EP-style model is expected to retain similar short-term predictive ability while producing lower failure rates, more stable long-horizon behavior, and more interpretable risk estimates.

## Release Boundary

This public version intentionally excludes code links, installation commands, exact acceptance criteria, specific output filenames, precise hyperparameters, and the staged expansion path toward larger empirical programs. Those details reveal too much of the executable research blueprint.

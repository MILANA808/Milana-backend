# AKSI Scientific Discovery Engine

## Why this branch exists

AKSI already contains runtime state tracking, semantic sampling, reproducibility
ideas, and provenance primitives. This branch adds a narrower scientific core:
**choose an observation because it separates competing explanations, then update
the hypothesis set only from the observed result.**

The intended primitive is *hypothesis-space surgery*: spend an experiment budget on
the measurement expected to eliminate the largest amount of uncertainty per unit
cost.

## What is implemented

- Explicit competing hypotheses with executable predictors.
- Candidate experiments with an input and cost.
- Deterministic partition scoring and information-gain-per-cost utility.
- Execution through an injected runner (the core does not assume a specific LLM).
- Evidence record containing predictions, observation, survivors, and SHA-256 hash.
- Explicit claim boundary: a survivor is not treated as truth.

## What is not claimed

This prototype is not by itself a new scientific discovery, AGI, consciousness,
or proof of superiority over existing AI systems. Prior-art review and empirical
benchmarking are required before making novelty claims.

## First falsifiable benchmark

Create a hidden rule in a small synthetic world. Give the engine multiple candidate
rules and a fixed experiment budget. Compare:

1. random experiment selection;
2. one-shot LLM/model answer;
3. AKSI discriminating selection.

Measure:
- hypotheses eliminated per experiment;
- information gain per cost;
- final identification rate;
- reproducibility across seeds;
- performance when the initial hypothesis set is wrong/incomplete.

The important test is not whether AKSI writes a better explanation. It is whether
the loop discovers which explanation survives contact with observations.

## Next research step

Add an **instrument compiler**: given the unresolved hypothesis space, select not only
the experiment input but the cheapest available measurement mechanism — simulation,
web source, API, code execution, or human measurement — and reject instruments that
cannot distinguish the active hypotheses.

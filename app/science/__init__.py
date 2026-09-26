"""AKSI Scientific Discovery Engine.

A deterministic, model-agnostic substrate for turning competing hypotheses into
discriminating experiments. Language models may propose hypotheses, but the core
does not trust prose as evidence.
"""
from .discovery import DiscoveryEngine, Hypothesis, Experiment, Observation
__all__ = ["DiscoveryEngine", "Hypothesis", "Experiment", "Observation"]

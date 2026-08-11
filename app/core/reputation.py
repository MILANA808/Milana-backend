"""EQS formula (from TZ) — classical metrics."""
from __future__ import annotations


def compute_eqs(
    h_avg: float = 3.2,
    reliability: float = 0.85,
    coherence: float = 0.8,
    age_factor: float = 0.9,
) -> float:
    """EQS = 0.30*(H_avg/5) + 0.35*reliability + 0.25*coherence + 0.10*age_factor"""
    eqs = (
        0.30 * (min(h_avg, 5.0) / 5.0)
        + 0.35 * reliability
        + 0.25 * coherence
        + 0.10 * age_factor
    )
    return round(min(1.0, max(0.0, eqs)), 4)

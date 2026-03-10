from __future__ import annotations

from dataclasses import dataclass


@dataclass
class QualificationConfig:
    threshold: int
    weights: dict[str, float]
    warmth_bands: dict[str, tuple[int, int]]


def compute_score(lead_fields: dict[str, str | None], cfg: QualificationConfig) -> int:
    raw = 0.0
    for field, weight in cfg.weights.items():
        value = lead_fields.get(field)
        if value and value.strip():
            raw += weight
    score = int(round(raw * 100))
    return min(100, max(0, score))


def resolve_warmth(score: int, warmth_bands: dict[str, tuple[int, int]]) -> str:
    for name, bounds in warmth_bands.items():
        start, end = bounds
        if start <= score <= end:
            return name
    return "cold"


def is_qualified(score: int, threshold: int) -> bool:
    return score >= threshold

from app.scoring import QualificationConfig, compute_score, is_qualified, resolve_warmth


def test_score_and_qualification() -> None:
    cfg = QualificationConfig(
        threshold=65,
        weights={"intent": 0.35, "timeline": 0.2, "budget": 0.25, "contact": 0.2},
        warmth_bands={"cold": (0, 39), "warm": (40, 69), "hot": (70, 100)},
    )
    score = compute_score({"intent": "x", "timeline": "x", "budget": None, "contact": "x"}, cfg)
    assert score == 75
    assert resolve_warmth(score, cfg.warmth_bands) == "hot"
    assert is_qualified(score, cfg.threshold)

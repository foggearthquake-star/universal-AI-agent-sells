from app.risk import detect_risk_flags


def test_risk_detection() -> None:
    text = "Нужна точная цена и договор сегодня"
    flags = detect_risk_flags(text, ["price_exact", "contract_legal", "urgent_deadline"])
    assert set(flags) == {"price_exact", "contract_legal", "urgent_deadline"}

from app.language import detect_language


def test_detect_language_ru() -> None:
    assert detect_language("Здравствуйте", ["ru", "en"]) == "ru"


def test_detect_language_en() -> None:
    assert detect_language("Hello there", ["ru", "en"]) == "en"

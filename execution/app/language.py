from __future__ import annotations

import re


CYRILLIC_RE = re.compile(r"[а-яА-ЯёЁ]")


def detect_language(text: str, allowed: list[str]) -> str:
    if "ru" in allowed and CYRILLIC_RE.search(text):
        return "ru"
    if "en" in allowed:
        return "en"
    return allowed[0] if allowed else "ru"

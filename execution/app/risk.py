from __future__ import annotations

import re


TRIGGER_PATTERNS: dict[str, str] = {
    "price_exact": r"(точн\w* цен|exact price|price quote|сколько точно)",
    "contract_legal": r"(договор|оферт|nda|contract|legal|юрид)"
    ,
    "complaint": r"(жалоб|претенз|плохо|refund|complaint|bad service)",
    "urgent_deadline": r"(срочно|сегодня|asap|urgent|дедлайн)"
}


def detect_risk_flags(text: str, enabled_triggers: list[str]) -> list[str]:
    lower = text.lower()
    result: list[str] = []
    for trigger in enabled_triggers:
        pattern = TRIGGER_PATTERNS.get(trigger)
        if pattern and re.search(pattern, lower):
            result.append(trigger)
    return result

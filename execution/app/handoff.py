from __future__ import annotations

from app.models import HandoffPayload, LeadState

RISK_RU = {
    "price_exact": "точная цена",
    "contract_legal": "договор/юридические вопросы",
    "complaint": "жалоба",
    "urgent_deadline": "срочный дедлайн",
    "out_of_kb": "вопрос вне базы знаний",
}

WARMTH_RU = {
    "cold": "холодный",
    "warm": "теплый",
    "hot": "горячий",
}

QUALIFICATION_RU = {
    "qualified": "квалифицирован",
    "not_qualified": "не квалифицирован",
}


def build_handoff_payload(lead_id: str, lead: LeadState) -> HandoffPayload:
    return HandoffPayload(
        title="New lead requires manager",
        lead_id=lead_id,
        score=lead.score,
        warmth=lead.warmth,
        qualification=lead.qualification.value,
        risk_flags=lead.risk_flags,
        summary=lead.summary or "No summary",
        fields={
            "intent": lead.intent,
            "timeline": lead.timeline,
            "budget": lead.budget,
            "contact": lead.contact,
        },
    )


def format_handoff_message(payload: HandoffPayload) -> str:
    risk_text = ", ".join(RISK_RU.get(flag, flag) for flag in payload.risk_flags) if payload.risk_flags else "-"
    warmth = WARMTH_RU.get(payload.warmth, payload.warmth)
    qualification = QUALIFICATION_RU.get(payload.qualification, payload.qualification)
    intent = payload.fields.get("intent") or "не удалось определить"
    timeline = payload.fields.get("timeline") or "не удалось определить"
    budget = payload.fields.get("budget") or "не удалось определить"
    contact = payload.fields.get("contact") or "не удалось определить"
    summary = payload.summary or "Краткая история диалога не сформирована."
    return (
        f"Лид #{payload.lead_id}\n"
        f"Оценка: {payload.score} ({warmth})\n"
        f"Статус: {qualification}\n"
        f"Риски: {risk_text}\n"
        f"Запрос: {intent}\n"
        f"Срок: {timeline}\n"
        f"Бюджет: {budget}\n"
        f"Контакт: {contact}\n"
        f"Сводка: {summary}"
    )

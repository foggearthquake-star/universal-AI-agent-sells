from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.crm import AmoCRMClient
from app.handoff import build_handoff_payload, format_handoff_message
from app.kb import KnowledgeBase
from app.language import detect_language
from app.llm import LLMClient
from app.models import HandoffStatus, LeadState, Qualification
from app.risk import detect_risk_flags
from app.scoring import QualificationConfig, compute_score, is_qualified, resolve_warmth
from app.storage import LeadRepository


FAQ_HINTS_RU = ("что", "как", "когда", "где", "почему", "сколько", "можно ли")
FAQ_HINTS_EN = ("what", "how", "when", "where", "why", "price", "can i")


def _load_client_config(client_id: str, clients_dir: Path) -> dict[str, Any]:
    path = clients_dir / f"{client_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing client config: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _looks_like_question(text: str) -> bool:
    low = text.lower().strip()
    if "?" in low:
        return True
    return any(token in low for token in FAQ_HINTS_RU + FAQ_HINTS_EN)


CONTACT_RE = re.compile(r"(@[A-Za-z0-9_]{3,}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|(?:\+?\d[\d\-\s()]{8,}\d))")
BUDGET_RE = re.compile(
    r"((?:бюджет|budget)\s*[:\-]?\s*[\d\s]+(?:[.,]\d+)?\s*(?:к|кк|тыс|млн|руб|₽|\$)?|[\d\s]+(?:[.,]\d+)?\s*(?:к|кк|тыс|млн)\b)"
)
TIMELINE_RE = re.compile(
    r"((?:срок|дедлайн|timeline)\s*[:\-]?\s*[^,.;]+|(?:сегодня|завтра|на этой неделе|на следующей неделе|within\s+\d+\s+(?:days?|weeks?|months?)))"
)


def _extract_fields(text: str, current: LeadState) -> LeadState:
    lowered = text.lower()
    parts = [part.strip() for part in re.split(r"[,\n;]+", text) if part.strip()]

    if current.contact is None:
        for part in parts:
            m = CONTACT_RE.search(part)
            if m:
                current.contact = m.group(1).strip()
                break

    if current.budget is None:
        for part in parts:
            if any(k in part.lower() for k in ["бюдж", "budget", "руб", "₽", "$", "к", "тыс", "млн"]):
                m = BUDGET_RE.search(part)
                current.budget = m.group(1).strip() if m else part
                break

    if current.timeline is None:
        # Prefer explicit timeline phrases ("срок ...", "дедлайн ...") over generic urgency words.
        for part in parts:
            pl = part.lower()
            if any(k in pl for k in ["срок", "дедлайн", "timeline"]):
                m = TIMELINE_RE.search(part)
                current.timeline = m.group(1).strip() if m else part
                break
    if current.timeline is None:
        for part in parts:
            if any(k in part.lower() for k in ["срок", "дедлайн", "today", "tomorrow", "недел", "дн", "месяц"]):
                m = TIMELINE_RE.search(part)
                current.timeline = m.group(1).strip() if m else part
                break

    if current.intent is None:
        intent_part = None
        for part in parts:
            pl = part.lower()
            if part == current.budget or part == current.timeline or part == current.contact:
                continue
            if any(k in pl for k in ["нуж", "хочу", "интерес", "need", "want", "looking for"]):
                intent_part = part
                break
        if intent_part is None and parts:
            for part in parts:
                if part not in {current.budget, current.timeline, current.contact}:
                    intent_part = part
                    break
        if intent_part:
            current.intent = intent_part

    # Fallbacks when everything came in one sentence.
    if current.contact is None:
        m = CONTACT_RE.search(text)
        if m:
            current.contact = m.group(1).strip()
    if current.budget is None and any(k in lowered for k in ["бюдж", "budget", "₽", "$", "руб"]):
        m = BUDGET_RE.search(text)
        if m:
            current.budget = m.group(1).strip()
    if current.timeline is None and any(k in lowered for k in ["срок", "дедлайн", "недел", "месяц", "дн", "today", "tomorrow"]):
        m = TIMELINE_RE.search(text)
        if m:
            current.timeline = m.group(1).strip()
    return current


def _next_question(lead: LeadState, lang: str) -> str | None:
    ru = {
        "intent": "Расскажите, какую задачу хотите решить?",
        "timeline": "Какие у вас сроки запуска/реализации?",
        "budget": "Какой ориентир по бюджету?",
        "contact": "Оставьте удобный контакт для менеджера.",
    }
    en = {
        "intent": "What goal are you trying to solve?",
        "timeline": "What timeline do you target for launch?",
        "budget": "What budget range do you consider?",
        "contact": "Please share your preferred contact.",
    }
    table = ru if lang == "ru" else en
    for field in ["intent", "timeline", "budget", "contact"]:
        if getattr(lead, field) is None:
            return table[field]
    return None


def _extract_json_object(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _telegram_contact(message: Message) -> str:
    user = message.from_user
    if user is None:
        return "telegram:user_unknown"
    if user.username:
        return f"@{user.username}"
    return f"telegram_id:{user.id}"


async def _build_faq_answer(chunks: list[str], lang: str, llm: LLMClient | None, question: str) -> str:
    text = "\n\n".join(chunks)[:2000]
    if llm is None:
        if lang == "ru":
            return f"Вот что нашёл в базе знаний:\n{text[:900]}"
        return f"Here is what I found in the knowledge base:\n{text[:900]}"

    system = (
        "You are a business assistant. Answer only from provided knowledge context. "
        "If context is insufficient, explicitly say so and suggest human handoff."
    )
    user = (
        f"Language: {lang}\n"
        f"Question: {question}\n\n"
        f"Knowledge context:\n{text}\n\n"
        "Return a concise and factual answer."
    )
    try:
        answer = await llm.complete(system, user)
        if answer:
            return answer
    except Exception:
        pass

    if lang == "ru":
        return f"Вот что нашёл в базе знаний:\n{text[:900]}"
    return f"Here is what I found in the knowledge base:\n{text[:900]}"


class LeadBot:
    def __init__(
        self,
        bot: Bot,
        repo: LeadRepository,
        crm: AmoCRMClient,
        client_id: str,
        clients_dir: Path,
        work_chat_id: int,
        work_topic_id: int | None,
        llm: LLMClient | None = None,
    ) -> None:
        self.bot = bot
        self.repo = repo
        self.crm = crm
        self.client_id = client_id
        self.clients_dir = clients_dir
        self.work_chat_id = work_chat_id
        self.work_topic_id = work_topic_id
        self.llm = llm
        self.sessions: dict[int, LeadState] = {}

        config = _load_client_config(client_id, clients_dir)
        q = config["qualification"]
        warmth = {k: tuple(v) for k, v in q["warmth_bands"].items()}
        self.q_cfg = QualificationConfig(
            threshold=q["threshold"],
            weights=q["weights"],
            warmth_bands=warmth,
        )
        self.allowed_languages = config.get("languages", ["ru", "en"])
        self.risk_triggers = config.get("risk_triggers", [])
        self.kb = KnowledgeBase(clients_dir / client_id / "kb")

    async def _reply(self, message: Message, lead: LeadState, text: str) -> None:
        await message.answer(text)
        lead.transcript.append({"role": "assistant", "text": text})

    async def _llm_extract_fields(self, lead: LeadState, latest_user_text: str) -> None:
        if self.llm is None:
            return

        history = "\n".join(
            f"{item.get('role', 'user')}: {item.get('text', '')}" for item in lead.transcript[-30:]
        )
        system = (
            "You extract lead qualification data from a chat history. "
            "Return strict JSON only. Do not include markdown."
        )
        user = (
            "Extract fields for a sales lead.\n"
            "If any field is unknown, set it to null.\n"
            "If context is insufficient, set context_sufficient=false.\n\n"
            "Return JSON with keys:\n"
            "intent, timeline, budget, contact, context_sufficient, context_note, history_summary.\n\n"
            f"Latest message:\n{latest_user_text}\n\n"
            f"Chat history:\n{history}"
        )
        try:
            raw = await self.llm.complete(system, user)
        except Exception:
            return

        parsed = _extract_json_object(raw)
        if not parsed:
            return

        for field in ["intent", "timeline", "budget", "contact"]:
            value = parsed.get(field)
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned and cleaned.lower() not in {"unknown", "null", "none", "неизвестно", "не удалось определить"}:
                    setattr(lead, field, cleaned)

        history_summary = parsed.get("history_summary")
        context_note = parsed.get("context_note")
        if isinstance(history_summary, str) and history_summary.strip():
            lead.summary = history_summary.strip()
        elif isinstance(context_note, str) and context_note.strip():
            lead.summary = context_note.strip()

    def _session(self, message: Message) -> LeadState:
        user_id = int(message.from_user.id)
        if user_id not in self.sessions:
            self.sessions[user_id] = LeadState(
                client_id=self.client_id,
                telegram_user_id=user_id,
                telegram_chat_id=int(message.chat.id),
                contact=_telegram_contact(message),
            )
        return self.sessions[user_id]

    async def _send_handoff(self, lead_id: str, lead: LeadState) -> bool:
        payload = build_handoff_payload(lead_id, lead)
        text = format_handoff_message(payload)
        sent_to_telegram = False
        if self.work_chat_id != 0:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Взять лид", callback_data=f"claim:{lead_id}")]
                ]
            )
            await self.bot.send_message(
                chat_id=self.work_chat_id,
                text=text,
                reply_markup=keyboard,
                message_thread_id=(self.work_topic_id if self.work_topic_id and self.work_topic_id > 0 else None),
            )
            sent_to_telegram = True
        await self.repo.mark_handoff_pending(lead_id)
        lead.handoff_status = HandoffStatus.PENDING_HUMAN
        sent_to_crm = await self.crm.create_lead(lead)
        return sent_to_telegram or sent_to_crm

    async def handle_message(self, message: Message) -> None:
        lead = self._session(message)
        text = (message.text or "").strip()
        if not text:
            return

        if not lead.contact:
            lead.contact = _telegram_contact(message)
        lead.language = detect_language(text, self.allowed_languages)
        lead.transcript.append({"role": "user", "text": text})
        await self._llm_extract_fields(lead, text)

        chunks = self.kb.search(text, top_k=3)
        if _looks_like_question(text):
            if chunks:
                answer = await _build_faq_answer([c.text for c in chunks], lead.language, self.llm, text)
                await self._reply(message, lead, answer)
            else:
                lead.summary = f"Out-of-KB question: {text[:280]}"
                lead.risk_flags = sorted(set(lead.risk_flags + ["out_of_kb"]))
                lead_id = await self.repo.upsert(lead)
                handed_off = await self._send_handoff(lead_id, lead)
                if lead.language == "ru":
                    if handed_off:
                        await self._reply(
                            message,
                            lead,
                            "В базе знаний нет точной информации по вопросу. Передаю диалог менеджеру."
                        )
                    else:
                        await self._reply(
                            message,
                            lead,
                            "В базе знаний нет точной информации по вопросу. Канал передачи менеджеру не настроен."
                        )
                else:
                    if handed_off:
                        await self._reply(
                            message,
                            lead,
                            "I do not have enough verified knowledge for this question. I will hand it to a manager."
                        )
                    else:
                        await self._reply(
                            message,
                            lead,
                            "I do not have enough verified knowledge for this question. Human handoff channel is not configured."
                        )
                return

        lead = _extract_fields(text, lead)
        if not lead.contact:
            lead.contact = _telegram_contact(message)
        lead.risk_flags = sorted(set(lead.risk_flags + detect_risk_flags(text, self.risk_triggers)))

        lead_fields = {
            "intent": lead.intent,
            "timeline": lead.timeline,
            "budget": lead.budget,
            "contact": lead.contact,
        }
        lead.score = compute_score(lead_fields, self.q_cfg)
        lead.warmth = resolve_warmth(lead.score, self.q_cfg.warmth_bands)
        lead.qualification = (
            Qualification.QUALIFIED if is_qualified(lead.score, self.q_cfg.threshold) else Qualification.NOT_QUALIFIED
        )

        if not lead.summary:
            lead.summary = (
                f"Запрос: {lead.intent or 'не удалось определить'}; "
                f"Срок: {lead.timeline or 'не удалось определить'}; "
                f"Бюджет: {lead.budget or 'не удалось определить'}; "
                f"Контакт: {lead.contact or 'не удалось определить'}"
            )
        lead_id = await self.repo.upsert(lead)

        if lead.risk_flags:
            handed_off = await self._send_handoff(lead_id, lead)
            if lead.language == "ru":
                if handed_off:
                    await self._reply(message, lead, "Передал ваш запрос менеджеру. Он подключится в течение часа.")
                else:
                    await self._reply(message, lead, "Нужна передача менеджеру, но канал эскалации еще не настроен.")
            else:
                if handed_off:
                    await self._reply(message, lead, "I have transferred your request to a manager. You will get a response within one hour.")
                else:
                    await self._reply(message, lead, "A human handoff is required, but escalation channel is not configured.")
            return

        ask = _next_question(lead, lead.language)
        if ask:
            await self._reply(message, lead, ask)
            return

        if lead.qualification == Qualification.QUALIFIED:
            handed_off = await self._send_handoff(lead_id, lead)
            if lead.language == "ru":
                if handed_off:
                    await self._reply(message, lead, "Спасибо, данных достаточно. Передаю диалог менеджеру.")
                else:
                    await self._reply(message, lead, "Спасибо, данных достаточно. Канал передачи менеджеру пока не настроен.")
            else:
                if handed_off:
                    await self._reply(message, lead, "Thanks, we have enough details. I am handing this over to a manager.")
                else:
                    await self._reply(message, lead, "Thanks, we have enough details. Human handoff channel is not configured yet.")
            return

        if lead.language == "ru":
            await self._reply(message, lead, "Чтобы лучше помочь, уточните детали задачи, сроков, бюджета и контакта.")
        else:
            await self._reply(message, lead, "To help further, please clarify your goal, timeline, budget, and contact.")

    async def handle_claim(self, callback: CallbackQuery) -> None:
        data = callback.data or ""
        _, lead_id = data.split(":", 1)
        manager = callback.from_user
        manager_username = f"@{manager.username}" if manager and manager.username else None
        manager_name = " ".join(
            part for part in [manager.first_name if manager else None, manager.last_name if manager else None] if part
        ).strip() or None
        await self.repo.mark_claimed(
            lead_id,
            claimed_by_user_id=(manager.id if manager else None),
            claimed_by_username=manager_username,
            claimed_by_name=manager_name,
        )
        await callback.answer("Лид назначен")
        manager_label = manager_username or manager_name or (f"id:{manager.id}" if manager else "неизвестный менеджер")
        if self.work_chat_id != 0:
            await self.bot.send_message(
                chat_id=self.work_chat_id,
                text=f"Лид #{lead_id} назначен менеджеру {manager_label}.",
                message_thread_id=(self.work_topic_id if self.work_topic_id and self.work_topic_id > 0 else None),
            )
        if callback.message:
            await callback.message.edit_reply_markup(reply_markup=None)


def build_dispatcher(lead_bot: LeadBot) -> Dispatcher:
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await message.answer(
            "Здравствуйте. Я помогу квалифицировать запрос и при необходимости передам менеджеру."
        )

    @dp.message(F.text)
    async def text_handler(message: Message) -> None:
        await lead_bot.handle_message(message)

    @dp.callback_query(F.data.startswith("claim:"))
    async def claim_handler(callback: CallbackQuery) -> None:
        await lead_bot.handle_claim(callback)

    return dp

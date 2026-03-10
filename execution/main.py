from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path

from aiogram import Bot

from app.bot import LeadBot, build_dispatcher
from app.config import settings
from app.crm import AmoCRMClient
from app.llm import LLMClient
from app.sla_monitor import SLAMonitor
from app.storage import LeadRepository


def ensure_default_config() -> None:
    clients_dir = settings.clients_dir
    clients_dir.mkdir(exist_ok=True)
    default_path = clients_dir / f"{settings.default_client_id}.json"
    if default_path.exists():
        return
    template = Path("client_config.example.json")
    if template.exists():
        default_path.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")


def ensure_default_kb() -> None:
    kb_dir = settings.clients_dir / settings.default_client_id / "kb"
    kb_dir.mkdir(parents=True, exist_ok=True)
    faq_file = kb_dir / "faq.md"
    if not faq_file.exists():
        faq_file.write_text(
            "# FAQ\n\nУкажите здесь материалы бизнеса: услуги, цены, процесс работы, ограничения.",
            encoding="utf-8",
        )


async def main() -> None:
    ensure_default_config()
    ensure_default_kb()

    repo = LeadRepository(settings.database_url)
    await repo.connect()

    bot = Bot(token=settings.telegram_bot_token)
    crm = AmoCRMClient(settings.amo_base_url, settings.amo_access_token)
    llm = LLMClient(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        base_url=settings.openai_base_url,
    )
    lead_bot = LeadBot(
        bot=bot,
        repo=repo,
        crm=crm,
        client_id=settings.default_client_id,
        clients_dir=settings.clients_dir,
        work_chat_id=settings.telegram_work_chat_id,
        work_topic_id=settings.telegram_work_topic_id,
        llm=llm,
    )
    dp = build_dispatcher(lead_bot)
    sla_monitor = SLAMonitor(
        bot=bot,
        repo=repo,
        work_chat_id=settings.telegram_work_chat_id,
        work_topic_id=settings.telegram_work_topic_id,
        sla_minutes=60,
        poll_seconds=120,
    )
    sla_task = asyncio.create_task(sla_monitor.run())

    try:
        await dp.start_polling(bot)
    finally:
        sla_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sla_task
        await repo.close()


if __name__ == "__main__":
    asyncio.run(main())

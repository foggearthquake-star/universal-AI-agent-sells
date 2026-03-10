from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from aiogram import Bot

from app.storage import LeadRepository


class SLAMonitor:
    def __init__(
        self,
        bot: Bot,
        repo: LeadRepository,
        work_chat_id: int,
        work_topic_id: int | None,
        sla_minutes: int = 60,
        poll_seconds: int = 120,
    ) -> None:
        self.bot = bot
        self.repo = repo
        self.work_chat_id = work_chat_id
        self.work_topic_id = work_topic_id
        self.sla_minutes = sla_minutes
        self.poll_seconds = poll_seconds

    async def run(self) -> None:
        while True:
            try:
                await self._check_once()
            except Exception as exc:
                # Keep monitor alive even if one pass fails.
                print(f"SLA monitor error: {exc}")
            await asyncio.sleep(self.poll_seconds)

    async def _check_once(self) -> None:
        if self.work_chat_id == 0:
            return

        overdue = await self.repo.find_overdue_pending_handoffs(self.sla_minutes)
        for row in overdue:
            created = row["handoff_created_at"]
            wait_min = 0
            if created is not None:
                wait_min = int((datetime.now(timezone.utc) - created).total_seconds() // 60)

            text = (
                "SLA ALERT: lead is waiting for manager longer than target\n"
                f"Lead ID: {row['id']}\n"
                f"Wait time: {wait_min} min\n"
                f"Score: {row['score']} ({row['warmth']})\n"
                f"Qualification: {row['qualification']}\n"
                f"Risk: {', '.join(row['risk_flags']) if row['risk_flags'] else '-'}\n"
                f"Summary: {row['summary'] or '-'}"
            )
            await self.bot.send_message(
                chat_id=self.work_chat_id,
                text=text,
                message_thread_id=(self.work_topic_id if self.work_topic_id and self.work_topic_id > 0 else None),
            )
            await self.repo.mark_handoff_alerted(str(row["id"]))

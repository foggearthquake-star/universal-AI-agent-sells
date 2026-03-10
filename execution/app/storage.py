from __future__ import annotations

import json
from datetime import datetime, timezone

import asyncpg

from app.models import HandoffStatus, LeadState


class LeadRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        self.pool = await asyncpg.create_pool(self.database_url)

    async def close(self) -> None:
        if self.pool:
            await self.pool.close()

    async def upsert(self, lead: LeadState) -> str:
        assert self.pool is not None
        row = await self.pool.fetchrow(
            """
            INSERT INTO lead_records (
                client_id, source, telegram_user_id, telegram_chat_id, language,
                intent, timeline, budget, contact, score, warmth, qualification,
                risk_flags, handoff_status, summary, transcript, updated_at
            ) VALUES (
                $1,$2,$3,$4,$5,
                $6,$7,$8,$9,$10,$11,$12,
                $13::jsonb,$14,$15,$16::jsonb,NOW()
            )
            ON CONFLICT (client_id, telegram_user_id)
            DO UPDATE SET
                source = EXCLUDED.source,
                telegram_chat_id = EXCLUDED.telegram_chat_id,
                language = EXCLUDED.language,
                intent = EXCLUDED.intent,
                timeline = EXCLUDED.timeline,
                budget = EXCLUDED.budget,
                contact = EXCLUDED.contact,
                score = EXCLUDED.score,
                warmth = EXCLUDED.warmth,
                qualification = EXCLUDED.qualification,
                risk_flags = EXCLUDED.risk_flags,
                handoff_status = EXCLUDED.handoff_status,
                summary = EXCLUDED.summary,
                transcript = EXCLUDED.transcript,
                updated_at = NOW()
            RETURNING id
            """,
            lead.client_id,
            lead.source,
            lead.telegram_user_id,
            lead.telegram_chat_id,
            lead.language,
            lead.intent,
            lead.timeline,
            lead.budget,
            lead.contact,
            lead.score,
            lead.warmth,
            lead.qualification.value,
            json.dumps(lead.risk_flags),
            lead.handoff_status.value,
            lead.summary,
            json.dumps(lead.transcript),
        )
        return str(row["id"])

    async def mark_handoff_pending(self, lead_id: str) -> None:
        assert self.pool is not None
        await self.pool.execute(
            """
            UPDATE lead_records
            SET handoff_status = $1,
                handoff_created_at = $2,
                updated_at = NOW()
            WHERE id = $3
            """,
            HandoffStatus.PENDING_HUMAN.value,
            datetime.now(tz=timezone.utc),
            int(lead_id),
        )

    async def mark_claimed(
        self,
        lead_id: str,
        claimed_by_user_id: int | None = None,
        claimed_by_username: str | None = None,
        claimed_by_name: str | None = None,
    ) -> None:
        assert self.pool is not None
        await self.pool.execute(
            """
            UPDATE lead_records
            SET handoff_status = $1,
                first_human_reply_at = $2,
                claimed_by_user_id = $3,
                claimed_by_username = $4,
                claimed_by_name = $5,
                updated_at = NOW()
            WHERE id = $6
            """,
            HandoffStatus.CLAIMED.value,
            datetime.now(tz=timezone.utc),
            claimed_by_user_id,
            claimed_by_username,
            claimed_by_name,
            int(lead_id),
        )

    async def find_overdue_pending_handoffs(self, sla_minutes: int) -> list[asyncpg.Record]:
        assert self.pool is not None
        return await self.pool.fetch(
            """
            SELECT id, telegram_user_id, score, warmth, qualification, risk_flags, summary, handoff_created_at
            FROM lead_records
            WHERE handoff_status = $1
              AND handoff_created_at IS NOT NULL
              AND handoff_alerted_at IS NULL
              AND handoff_created_at <= NOW() - make_interval(mins => $2)
            ORDER BY handoff_created_at ASC
            """,
            HandoffStatus.PENDING_HUMAN.value,
            sla_minutes,
        )

    async def mark_handoff_alerted(self, lead_id: str) -> None:
        assert self.pool is not None
        await self.pool.execute(
            """
            UPDATE lead_records
            SET handoff_alerted_at = $1,
                updated_at = NOW()
            WHERE id = $2
            """,
            datetime.now(tz=timezone.utc),
            int(lead_id),
        )

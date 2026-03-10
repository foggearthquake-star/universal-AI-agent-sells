from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.models import LeadState


class AmoCRMClient:
    def __init__(self, base_url: str | None, access_token: str | None) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.access_token = access_token

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.access_token)

    def build_payload(self, lead: LeadState) -> dict[str, Any]:
        return {
            "name": f"Lead {lead.telegram_user_id}",
            "custom_fields_values": [
                {"field_code": "LEAD_INTENT", "values": [{"value": lead.intent or ""}]},
                {"field_code": "LEAD_TIMELINE", "values": [{"value": lead.timeline or ""}]},
                {"field_code": "LEAD_BUDGET", "values": [{"value": lead.budget or ""}]},
                {"field_code": "LEAD_CONTACT", "values": [{"value": lead.contact or ""}]},
                {"field_code": "LEAD_SCORE", "values": [{"value": str(lead.score)}]},
            ],
        }

    async def create_lead(self, lead: LeadState) -> bool:
        if not self.enabled:
            return False
        payload = self.build_payload(lead)
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.base_url}/api/v4/leads"
        async with httpx.AsyncClient(timeout=10) as client:
            for attempt in range(3):
                try:
                    response = await client.post(url, headers=headers, json=[payload])
                    if response.status_code < 300:
                        return True
                except httpx.HTTPError:
                    pass
                if attempt < 2:
                    await asyncio.sleep(1.5 * (attempt + 1))
        return False

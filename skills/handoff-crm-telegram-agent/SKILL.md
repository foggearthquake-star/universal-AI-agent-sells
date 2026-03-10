---
name: handoff-crm-telegram-agent
description: Transfer qualified or risky leads to human managers by posting structured lead cards in Telegram and creating/updating leads in amoCRM with retry-safe payload mapping. Use when implementing operational handoff flows from AI to sales teams.
---

Read `references/handoff-contracts.md` before implementation.

Workflow:
1. Build a manager-facing lead card (score, warmth, fields, risks, summary).
2. Publish to Telegram work chat with claim action.
3. Push mapped payload to amoCRM.
4. Update handoff state to `pending_human` and track SLA markers.

Escalate immediately on risk triggers.

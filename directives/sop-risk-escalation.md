# SOP: Risk and Escalation

## Mandatory Risk Triggers
- Pricing negotiation requiring exact quote.
- Contract/legal terms.
- Complaints or dissatisfaction.
- Urgent requests with strict deadlines.

## Escalation Policy
- Escalate immediately when at least one trigger is detected.
- Send card to Telegram work chat with claim action.
- Create or update lead in amoCRM with risk notes.
- Mark `handoff_status` as `pending_human`.

## SLA
- Human manager response target: up to 1 hour.
- Track `handoff_created_at` and `first_human_reply_at`.
- Raise alert for unclaimed cards older than SLA.

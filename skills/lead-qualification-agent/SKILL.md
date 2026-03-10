---
name: lead-qualification-agent
description: Qualify inbound leads in chat by collecting intent, timeline, budget, and contact; compute 0-100 score with client-specific weights; classify warmth and qualification; and produce concise qualification reasoning. Use when building or operating conversational lead qualification flows.
---

Read `references/qualification-flow.md` before implementation.

Load client profile from a JSON config with fields, weights, thresholds, and risk triggers.

Execute this sequence:
1. Extract structured fields from free-form user messages.
2. Ask one missing high-impact question per turn.
3. Compute score and warmth.
4. Set `qualified` or `not_qualified`.
5. Output compact reasoning tied to observed data.

When uncertainty is high, ask one clarification instead of guessing.

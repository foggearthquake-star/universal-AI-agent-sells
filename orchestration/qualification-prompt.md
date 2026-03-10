# Qualification Prompt Template

Inputs:
- client_config
- lead_state
- latest_user_message

Tasks:
1. Extract missing fields: intent, timeline, budget, contact.
2. Ask at most one high-impact follow-up question per turn.
3. Score lead with configured weights.
4. Return JSON:
   - extracted_fields
   - score
   - warmth
   - qualification
   - reasoning
   - risk_flags

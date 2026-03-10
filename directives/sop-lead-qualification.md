# SOP: Lead Qualification

## Objective
- Collect lead intent, timeline, budget, and contact details.
- Compute lead score from 0 to 100.
- Mark lead as `qualified` or `not_qualified`.
- Route conversation to human on risk triggers.

## Required Data Points
- `intent`: What client wants.
- `timeline`: Desired launch or delivery date.
- `budget`: Budget range or willingness to discuss budget.
- `contact`: Preferred callback contact.

## Qualification Rules
- Use weighted scoring from `client_config.json`.
- Normalize score to `[0, 100]`.
- Treat lead as `qualified` when score is at or above configured threshold.
- Return short reasoning that cites captured fields and confidence.

## Warmth Classification
- `cold`: 0-39
- `warm`: 40-69
- `hot`: 70-100
- Allow per-client overrides.

## Handoff Rules
- Always handoff when any risk trigger is detected.
- Also handoff when lead is qualified and asks for human manager.
- Include full lead card, risk flags, and short transcript summary.

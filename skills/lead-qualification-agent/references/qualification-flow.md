# Qualification Flow Reference

## Inputs
- User text stream
- Client config (weights, threshold, mandatory fields)

## Outputs
- Extracted fields
- Score 0-100
- Warmth: cold/warm/hot
- Qualification decision
- Short reasoning

## Extraction hints
- `intent`: desired business outcome or service request
- `timeline`: date, urgency, deadline, period
- `budget`: range, cap, willingness to discuss
- `contact`: phone, Telegram handle, email

## Decision
- Compute weighted score from present validated fields.
- Mark qualified when score >= threshold.

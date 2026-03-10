# RAG Policy

## Retrieval
- Use semantic or lexical retrieval on KB chunks.
- Select top chunks with clear relevance.

## Response constraints
- Cite only facts present in chunks.
- Keep answer concise and actionable.
- Preserve user language (RU/EN).

## Out-of-knowledge
- Say information is unavailable in current KB.
- Offer transfer to human manager.
- Do not guess prices, legal terms, or guarantees.

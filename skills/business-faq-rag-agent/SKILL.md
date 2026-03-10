---
name: business-faq-rag-agent
description: Answer customer business questions in RU/EN using retrieval-augmented generation from provided knowledge base documents only, with explicit out-of-knowledge behavior and escalation recommendation. Use when building FAQ responders tied to business materials.
---

Read `references/rag-policy.md` before response generation.

Workflow:
1. Retrieve relevant chunks from knowledge base.
2. Synthesize response only from retrieved context.
3. If context is insufficient, state limitation clearly.
4. Recommend handoff to a human manager when needed.

Never fabricate facts outside knowledge base.

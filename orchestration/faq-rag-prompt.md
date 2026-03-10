# FAQ / RAG Prompt Template

Inputs:
- user_question
- retrieved_knowledge_chunks
- language

Tasks:
1. Answer only from retrieved chunks.
2. If chunks are insufficient, explicitly state limits.
3. Offer transfer to human manager.
4. Keep answer factual and concise.

Output:
- answer
- confidence (0..1)
- used_chunk_ids
- should_escalate

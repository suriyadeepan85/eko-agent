#!/usr/bin/env python3
"""
Baseline naive single-pass RAG.

This is a deliberately simplistic implementation to serve as a comparison point
for the full agentic pipeline. It demonstrates what single-pass RAG gets right
(modern LLMs can reason over conflicting documents) and what it lacks:

WHAT IT LACKS (why the full pipeline is needed):

1. No explicit precedence rules
   - Relies on LLM to infer date-based precedence
   - No audit trail showing which rule was applied
   - Can't systematically handle authority_tier precedence

2. No validation/grounding enforcement
   - Accepts whatever the LLM generates
   - No claim-by-claim source verification
   - Can't detect unsupported claims or hallucinations

3. No retry mechanism
   - One shot only
   - If generation fails, no recovery
   - No iterative refinement

4. No decomposition
   - Handles compound questions as-is
   - Can't break down complex queries
   - May miss relevant documents for multi-part questions

5. No run records
   - No explainability trace
   - No audit trail for compliance (US3/US4/US6)
   - Can't debug failures systematically

6. No failure detection
   - Doesn't track insufficient_retrieval
   - Doesn't recognize when answer is uncertain
   - No typed failure modes

WHEN THIS IS SUFFICIENT:

For simple questions where:
- Both conflicting documents are retrieved
- LLM correctly infers precedence
- No validation required
- No audit trail needed

For the test corpus, Claude Sonnet 4.5 handles many cases well because both
documents (C3 and D4) are retrieved and it can reason about dates. However,
production systems need the full pipeline for compliance, auditability, and
systematic failure handling.
"""

import sys
from . import retrieval
from .aws_client import get_bedrock_client, get_model_id


def baseline_rag(question: str, k: int = 5, max_tokens: int = 500) -> str:
    """Single-pass RAG: retrieve, generate, done.

    Args:
        question: User question
        k: Number of chunks to retrieve
        max_tokens: Max tokens for generation

    Returns:
        Generated answer (unvalidated)
    """
    # Step 1: Retrieve chunks
    print(f"\n[Retrieval] Querying for: {question}")
    chunks = retrieval.query(question, k=k)

    if not chunks:
        return "No relevant documents found."

    print(f"[Retrieval] Retrieved {len(chunks)} chunks:")
    for chunk in chunks:
        print(f"  - {chunk['doc_id']} (score: {chunk['score']:.4f})")

    # Step 2: Build prompt with retrieved context
    context = "\n\n---\n\n".join([
        f"Document: {chunk['doc_id']}\n{chunk['text']}"
        for chunk in chunks
    ])

    prompt = f"""Answer the question based on the provided documents.

Documents:

{context}

Question: {question}

Answer:"""

    # Step 3: Generate answer (single call, no retry)
    print(f"\n[Generation] Calling Bedrock...")
    client = get_bedrock_client()

    response = client.converse(
        modelId=get_model_id(),
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens},
    )

    answer = response["output"]["message"]["content"][0]["text"]
    tokens = response["usage"]

    print(f"[Generation] Tokens: {tokens}")

    return answer


def main():
    """CLI entrypoint."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.baseline '<question>'")
        print("\nExample questions:")
        print("  'How many days of rental am I covered for and at what rate?'")
        print("  'What is the total loss threshold?'")
        print("  'Do I pay a deductible for a cracked windshield?'")
        sys.exit(1)

    question = sys.argv[1]

    print("=" * 60)
    print("BASELINE NAIVE RAG")
    print("=" * 60)

    answer = baseline_rag(question)

    print("\n" + "=" * 60)
    print("ANSWER:")
    print("=" * 60)
    print(answer)
    print("=" * 60)


if __name__ == "__main__":
    main()

"""
Reasoner agent - LLM-based answer generation with precedence rules.
"""

import boto3
import json
import logging


def reason(question: str, chunks: list[dict], context: list[dict],
           prior_attempt: dict = None) -> dict:
    """Generate answer from chunks, applying precedence rules.

    Args:
        question: Original question
        chunks: Pooled chunks with metadata
        context: Conversation history
        prior_attempt: {'draft': str, 'reason': str} if retry

    Returns:
        {'draft': str, 'claims': [{'claim': str, 'doc_ids': list[str]}],
         'precedence': [{'rule': str, 'winner': str, 'over': str}]}
    """
    chunks_text = "\n\n".join([
        f"[{c['doc_id']}] (effective: {c.get('effective_date', 'N/A')}, "
        f"authority: {c.get('authority_tier', 'N/A')})\n{c['text']}"
        for c in chunks
    ])

    prompt = f"""Answer the question based on the provided documents. Apply precedence rules when documents conflict.

PRECEDENCE RULES (in order):
1. Later effective_date wins (e.g., 2026-05-01 beats 2025-07-01)
2. More specific beats general (use judgment)
3. Higher authority tier wins: policy > procedure > reference > comms

DOCUMENTS:

{chunks_text}

QUESTION: {question}"""

    if prior_attempt:
        prompt += f"""

PREVIOUS ATTEMPT WAS REJECTED:
Draft: {prior_attempt['draft']}
Reason: {prior_attempt['reason']}

Please revise to address the rejection reason."""

    prompt += """

IMPORTANT: Respond with ONLY a JSON object, no other text before or after.

JSON format:
{
  "draft": "Your answer here",
  "claims": [
    {"claim": "Specific factual statement", "doc_ids": ["D4-...", ...]},
    ...
  ],
  "precedence": [
    {"rule": "later_effective_date", "winner": "D4-...", "over": "C3-..."},
    ...
  ]
}

Each claim must cite its source documents. The precedence array can be empty [] if no conflicts."""

    client = boto3.client("bedrock-runtime", region_name="us-east-1")
    response = client.converse(
        modelId="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 1000}
    )

    text = response["output"]["message"]["content"][0]["text"]

    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    result = json.loads(text)

    if 'precedence' not in result:
        result['precedence'] = []

    logging.info(f"Reasoner: generated {len(result['claims'])} claims, "
                 f"applied {len(result.get('precedence', []))} precedence rules")

    return result

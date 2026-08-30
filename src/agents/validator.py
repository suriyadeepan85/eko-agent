"""
Validator agent - stateless LLM-based claim verification.
"""

import json
import logging
from ..aws_client import get_bedrock_client, get_model_id


def validate(draft: str, claims: list[dict], chunks: list[dict]) -> dict:
    """Validate each claim is grounded in provided chunks.

    STATELESS: No context, no attempt count, no memory.

    Args:
        draft: Reasoner's draft answer
        claims: List of claim dicts with doc_ids
        chunks: Available chunks

    Returns:
        {'verdict': 'accepted'|'rejected', 'reason': str|None}
    """
    chunks_text = "\n\n".join([
        f"[{c['doc_id']}]\n{c['text']}"
        for c in chunks
    ])

    claims_text = "\n".join([
        f"{i+1}. {claim['claim']} (cites: {', '.join(claim['doc_ids'])})"
        for i, claim in enumerate(claims)
    ])

    prompt = f"""Verify each claim is grounded in the provided documents.

DOCUMENTS:

{chunks_text}

CLAIMS TO VERIFY:

{claims_text}

For each claim, check:
1. Is the claim stated or clearly implied in the cited documents?
2. Are the cited doc_ids correct?

IMPORTANT: Respond with ONLY a JSON object, no other text before or after.

JSON format:
{{
  "verdict": "accepted",
  "reason": null
}}

OR

{{
  "verdict": "rejected",
  "reason": "Brief explanation of which claim(s) are unsupported"
}}

Accept if ALL claims are supported. Reject if ANY claim is unsupported or cites wrong documents."""

    client = get_bedrock_client()
    response = client.converse(
        modelId=get_model_id(),
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 500}
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

    try:
        result = json.loads(text)
    except json.JSONDecodeError as e:
        logging.error(f"Validator JSON parse error: {e}")
        logging.error(f"Raw response: {text[:500]}")
        raise

    logging.info(f"Validator: verdict={result['verdict']}")

    return result

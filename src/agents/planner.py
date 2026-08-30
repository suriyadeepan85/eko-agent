"""
Planner agent - LLM-based query decomposition.
"""

import json
import logging
from ..aws_client import get_bedrock_client, get_model_id


def plan(question: str, context: list[dict]) -> dict:
    """Decompose question into sub-questions if needed.

    Args:
        question: User question
        context: Conversation history (empty for single-turn)

    Returns:
        {'decomposed': bool, 'sub_questions': list[str]}
    """
    prompt = f"""Analyze this question and decide if it needs decomposition.

Question: {question}

If the question asks multiple distinct things that require separate searches, decompose it into sub-questions.
Otherwise, pass it through as a single query.

Examples:
- "How many days of rental am I covered for and at what rate?"
  → DECOMPOSE: ["What is the rental coverage duration?", "What is the rental reimbursement rate?"]

- "What is the total loss threshold?"
  → DIRECT: ["What is the total loss threshold?"]

IMPORTANT: Respond with ONLY a JSON object, no other text before or after.

JSON format:
{{"decomposed": true/false, "sub_questions": ["..."]}}"""

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

    result = json.loads(text)

    logging.info(f"Planner: decomposed={result['decomposed']}, "
                 f"sub_questions={len(result['sub_questions'])}")

    return result

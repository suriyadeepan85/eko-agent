"""
Pooling module - deterministic chunk deduplication.
"""


def pool_chunks(retrievals: list[tuple[str, list[dict]]]) -> list[dict]:
    """Deduplicate chunks across retrievals, keeping highest score.

    Args:
        retrievals: List of (sub_question, chunks) tuples

    Returns:
        Deduplicated chunks with sub_question tags
    """
    doc_map = {}

    for sub_q, chunks in retrievals:
        for chunk in chunks:
            doc_id = chunk['doc_id']

            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    **chunk,
                    'sub_questions': [sub_q]
                }
            else:
                if chunk['score'] > doc_map[doc_id]['score']:
                    doc_map[doc_id].update(chunk)

                if sub_q not in doc_map[doc_id]['sub_questions']:
                    doc_map[doc_id]['sub_questions'].append(sub_q)

    pooled = sorted(doc_map.values(), key=lambda c: c['score'], reverse=True)

    return pooled

import logging
from . import storage

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Similarity floor - set empirically after testing Q3 vs Q2/Q10
# Measured empirically by running all test queries.
#
# Observed scores:
#   Q3 best score:   0.5005 (diminished value - unanswerable)
#   Q2 best score:   0.5750 (rental limits)
#   Q10 best score:  0.5506 (catastrophe/glass)
#   Q7 (total loss): 0.4633 (A4), 0.4546 (B4), 0.4497 (B3)
#
# FINDING: Q3 (unanswerable) scores HIGHER than Q7 (answerable multi-doc).
# This means similarity to individual documents doesn't indicate answerability.
# Setting floor at 0.44 to preserve all answerable queries while filtering
# very poor matches. This is below Q7's lowest score (B3: 0.4497) but above
# truly irrelevant results.
SIMILARITY_FLOOR = 0.44


def _distance_to_similarity(distance: float) -> float:
    """Convert Chroma L2 distance to similarity score.

    Formula: 1 / (1 + distance)

    This gives intuitive 0-1 range where:
    - 1.0 = perfect match (distance = 0)
    - 0.5 = moderate similarity (distance = 1)
    - Approaches 0 as distance increases

    Returns:
        Similarity score in range (0, 1]
    """
    return 1.0 / (1.0 + distance)


def _detect_signals(results: list[dict], filters_applied: bool,
                    original_count: int, floor: float) -> list[str]:
    """Detect retrieval failure conditions.

    Returns list of signal names:
    - 'insufficient_retrieval': No chunks cleared the similarity floor
    - 'weak_retrieval': Best score within 0.05 of floor
    - 'filtered_empty': Filters eliminated all candidates
    """
    signals = []

    if original_count > 0 and len(results) == 0:
        if filters_applied:
            signals.append('filtered_empty')
        else:
            signals.append('insufficient_retrieval')

    if len(results) > 0 and results[0]['score'] < floor + 0.05:
        signals.append('weak_retrieval')

    return signals


def query(text: str, k: int = 5, filters: dict | None = None) -> list[dict]:
    """Return up to k chunks, ordered by relevance (higher score = better).

    Args:
        text: Query text to search for
        k: Maximum number of results (default 5)
        filters: Optional metadata filters (Chroma where clause)

    Returns:
        List of dicts with: text, doc_id, title, effective_date,
        authority_tier, form, score (similarity 0-1, higher = better)

    Score convention: Similarity where 1.0 = perfect match, 0.0 = no match.
    Converted from Chroma distance using: 1 / (1 + distance)
    """
    client = storage.get_chroma_client()
    collection = client.get_collection("acme_auto_corpus")

    chroma_results = collection.query(
        query_texts=[text],
        n_results=k,
        where=filters,
        include=['documents', 'metadatas', 'distances']
    )

    original_count = len(chroma_results['ids'][0])
    processed_results = []

    for i in range(len(chroma_results['ids'][0])):
        doc_text = chroma_results['documents'][0][i]
        metadata = chroma_results['metadatas'][0][i]
        distance = chroma_results['distances'][0][i]

        score = _distance_to_similarity(distance)

        result = {
            **metadata,
            'text': doc_text,
            'score': score
        }
        processed_results.append(result)

    filtered_results = [r for r in processed_results if r['score'] >= SIMILARITY_FLOOR]

    filtered_results.sort(key=lambda r: r['score'], reverse=True)

    signals = _detect_signals(
        filtered_results,
        filters is not None,
        original_count,
        SIMILARITY_FLOOR
    )

    if signals:
        logging.debug(f"Retrieval signals: {signals}")

    return filtered_results

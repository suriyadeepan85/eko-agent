"""
Tests for retrieval done-criteria from specs/retrieval-spec.md.

These tests verify retrieval returns expected documents:
- "rental per day limit" returns both C3 and D4
- "total loss threshold" returns B3, B4, and A4
- Returned chunks have all five metadata fields plus score

Tests run against existing chroma_db and do not modify it.
"""

import pytest
from src import retrieval


def test_rental_query_returns_c3_and_d4():
    """Verify "rental per day limit" returns both C3 and D4.

    This is Q2's primary test case. Both documents must surface
    for the reasoner to apply precedence (D4 over C3).
    """
    results = retrieval.query("rental per day limit", k=5)

    doc_ids = [chunk['doc_id'] for chunk in results]

    # Check both C3 and D4 are present
    c3_found = any(doc_id.startswith('C3') for doc_id in doc_ids)
    d4_found = any(doc_id.startswith('D4') for doc_id in doc_ids)

    assert c3_found, f"C3 not found in results for 'rental per day limit'. Got: {doc_ids}"
    assert d4_found, f"D4 not found in results for 'rental per day limit'. Got: {doc_ids}"


def test_total_loss_query_returns_b3_b4_a4():
    """Verify "total loss threshold" returns B3, B4, and A4.

    This is Q7's test case. All three documents must surface:
    - B3 and B4: different versions with different thresholds
    - A4: state-specific override for Meridian
    """
    results = retrieval.query("total loss threshold", k=8)

    doc_ids = [chunk['doc_id'] for chunk in results]

    # Check all three are present
    b3_found = any(doc_id.startswith('B3') for doc_id in doc_ids)
    b4_found = any(doc_id.startswith('B4') for doc_id in doc_ids)
    a4_found = any(doc_id.startswith('A4') for doc_id in doc_ids)

    assert b3_found, f"B3 not found in results for 'total loss threshold'. Got: {doc_ids}"
    assert b4_found, f"B4 not found in results for 'total loss threshold'. Got: {doc_ids}"
    assert a4_found, f"A4 not found in results for 'total loss threshold'. Got: {doc_ids}"


def test_returned_chunks_have_required_fields():
    """Verify every returned chunk has all five metadata fields plus score."""
    results = retrieval.query("rental coverage", k=5)

    assert len(results) > 0, "No results returned"

    required_fields = ['doc_id', 'title', 'effective_date', 'authority_tier', 'form', 'score']

    for i, chunk in enumerate(results):
        for field in required_fields:
            assert field in chunk, f"Chunk {i} missing field '{field}'. Has: {chunk.keys()}"
            assert chunk[field] is not None, f"Chunk {i} has null '{field}'"


def test_returned_chunks_have_text():
    """Verify every returned chunk includes the document text."""
    results = retrieval.query("insurance policy", k=3)

    assert len(results) > 0, "No results returned"

    for i, chunk in enumerate(results):
        assert 'text' in chunk, f"Chunk {i} missing 'text' field"
        assert chunk['text'] is not None, f"Chunk {i} has null 'text'"
        assert len(chunk['text']) > 0, f"Chunk {i} has empty 'text'"
        # Documents are ~200 words, should be at least 100 chars
        assert len(chunk['text']) > 100, f"Chunk {i} text suspiciously short: {len(chunk['text'])} chars"


def test_scores_are_similarity_not_distance():
    """Verify scores are similarity (higher = better), not raw Chroma distance.

    Per specs/retrieval-spec.md: "Score convention: Similarity where 1.0 =
    perfect match, 0.0 = no match. Converted from Chroma distance using: 1 / (1 + distance)"
    """
    results = retrieval.query("rental", k=5)

    assert len(results) > 0, "No results returned"

    for i, chunk in enumerate(results):
        score = chunk['score']
        doc_id = chunk['doc_id']

        # Similarity scores should be in range (0, 1]
        assert 0 < score <= 1.0, \
            f"Chunk {i} ({doc_id}): score {score} not in range (0, 1]. Are these raw distances?"

        # Scores should be reasonably high for relevant matches
        # The similarity floor is 0.44, so returned chunks should be above that
        assert score > 0.44, \
            f"Chunk {i} ({doc_id}): score {score} below similarity floor (0.44)"


def test_results_ordered_by_score():
    """Verify results are ordered by score descending (best match first)."""
    results = retrieval.query("total loss threshold", k=5)

    assert len(results) >= 2, "Need at least 2 results to test ordering"

    scores = [chunk['score'] for chunk in results]

    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i + 1], \
            f"Results not properly ordered: score[{i}]={scores[i]:.4f} < score[{i+1}]={scores[i+1]:.4f}"


def test_similarity_floor_filters_poor_matches():
    """Verify the similarity floor (0.44) filters out irrelevant results.

    All returned chunks should have scores above the floor.
    """
    # Query for something that might have poor matches
    results = retrieval.query("irrelevant unrelated query xyz", k=10)

    # If any results are returned, they should all be above the floor
    for i, chunk in enumerate(results):
        score = chunk['score']
        doc_id = chunk['doc_id']

        assert score > 0.44, \
            f"Chunk {i} ({doc_id}): score {score} below similarity floor (0.44). Floor not applied?"


def test_k_parameter_limits_results():
    """Verify k parameter correctly limits number of results."""
    k = 3
    results = retrieval.query("insurance", k=k)

    assert len(results) <= k, f"Expected at most {k} results, got {len(results)}"


def test_no_duplicate_doc_ids_in_results():
    """Verify no duplicate documents in a single retrieval result.

    Each document is a single chunk, so doc_ids should be unique.
    """
    results = retrieval.query("rental coverage policy", k=10)

    doc_ids = [chunk['doc_id'] for chunk in results]
    unique_doc_ids = set(doc_ids)

    assert len(doc_ids) == len(unique_doc_ids), \
        f"Duplicate doc_ids found: {[did for did in doc_ids if doc_ids.count(did) > 1]}"

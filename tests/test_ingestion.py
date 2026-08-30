"""
Tests for ingestion done-criteria from specs/ingestion-spec.md.

These tests verify the corpus was ingested correctly:
- 20 chunks total
- All five metadata fields populated on every chunk
- No null effective_date
- D4's effective_date is 2026-05-01 (not 2026-04-15)

Tests run against existing chroma_db and do not modify it.
"""

import pytest
from src import storage


def test_chunk_count_is_20():
    """Verify collection contains exactly 20 chunks."""
    client = storage.get_chroma_client()
    collection = client.get_collection("acme_auto_corpus")

    count = collection.count()
    assert count == 20, f"Expected 20 chunks, found {count}"


def test_all_chunks_have_five_metadata_fields():
    """Verify every chunk has doc_id, title, effective_date, authority_tier, form."""
    client = storage.get_chroma_client()
    collection = client.get_collection("acme_auto_corpus")

    # Get all chunks
    results = collection.get(
        include=['metadatas']
    )

    metadatas = results['metadatas']
    assert len(metadatas) == 20, f"Expected 20 chunks, got {len(metadatas)}"

    required_fields = ['doc_id', 'title', 'effective_date', 'authority_tier', 'form']

    for i, metadata in enumerate(metadatas):
        for field in required_fields:
            assert field in metadata, f"Chunk {i} missing field '{field}'"
            assert metadata[field] is not None, f"Chunk {i} has null '{field}'"
            assert metadata[field] != '', f"Chunk {i} has empty '{field}'"


def test_no_null_effective_date():
    """Verify no chunk has null effective_date."""
    client = storage.get_chroma_client()
    collection = client.get_collection("acme_auto_corpus")

    results = collection.get(
        include=['metadatas']
    )

    for i, metadata in enumerate(results['metadatas']):
        effective_date = metadata.get('effective_date')
        assert effective_date is not None, f"Chunk {i} (doc_id: {metadata.get('doc_id')}) has null effective_date"
        assert effective_date != '', f"Chunk {i} (doc_id: {metadata.get('doc_id')}) has empty effective_date"


def test_d4_effective_date_is_correct():
    """Verify D4's effective_date is 2026-05-01 (not the issued date 2026-04-15).

    D4 has two dates in its header:
    - Issued: 2026-04-15
    - Effective for losses on or after: 2026-05-01

    The parser must extract the effective date, not the issued date.
    """
    client = storage.get_chroma_client()
    collection = client.get_collection("acme_auto_corpus")

    # Get all chunks and find D4
    results = collection.get(
        include=['metadatas']
    )

    d4_found = False
    for metadata in results['metadatas']:
        if metadata['doc_id'].startswith('D4'):
            d4_found = True
            effective_date = metadata['effective_date']
            assert effective_date == '2026-05-01', \
                f"D4 effective_date is {effective_date}, should be 2026-05-01 (not the issued date 2026-04-15)"
            break

    assert d4_found, "D4 document not found in collection"


def test_metadata_field_types():
    """Verify metadata fields have expected string type."""
    client = storage.get_chroma_client()
    collection = client.get_collection("acme_auto_corpus")

    results = collection.get(
        include=['metadatas']
    )

    for i, metadata in enumerate(results['metadatas']):
        doc_id = metadata.get('doc_id')

        # All fields should be strings
        assert isinstance(metadata['doc_id'], str), f"Chunk {i}: doc_id is not string"
        assert isinstance(metadata['title'], str), f"Chunk {i} ({doc_id}): title is not string"
        assert isinstance(metadata['effective_date'], str), f"Chunk {i} ({doc_id}): effective_date is not string"
        assert isinstance(metadata['authority_tier'], str), f"Chunk {i} ({doc_id}): authority_tier is not string"
        assert isinstance(metadata['form'], str), f"Chunk {i} ({doc_id}): form is not string"


def test_authority_tier_values():
    """Verify authority_tier has valid values: policy, procedure, reference, comms."""
    client = storage.get_chroma_client()
    collection = client.get_collection("acme_auto_corpus")

    results = collection.get(
        include=['metadatas']
    )

    valid_tiers = ['policy', 'procedure', 'reference', 'comms']

    for i, metadata in enumerate(results['metadatas']):
        doc_id = metadata.get('doc_id')
        authority_tier = metadata['authority_tier']

        assert authority_tier in valid_tiers, \
            f"Chunk {i} ({doc_id}): authority_tier '{authority_tier}' not in {valid_tiers}"

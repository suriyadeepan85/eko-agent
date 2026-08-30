# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Enterprise Knowledge Ops Agent** — A retrieval-augmented generation (RAG) system demonstrating production-grade document reasoning over a deliberately-adversarial synthetic insurance corpus. Uses AWS Bedrock (Claude models) and ChromaDB for vector storage.

**Not a production system.** All content is synthetic: placeholder carrier (Acme Mutual), fictional state (Meridian). Designed to fail in observable ways to validate retrieval and reasoning architecture.

## Environment

- **Python**: 3.14+ with virtual environment at `.venv/`
- **Backend**: AWS Bedrock (us-east-1) — no Anthropic API key used
- **Model**: Claude Sonnet 4.5 (us.anthropic.claude-sonnet-4-5-20250929-v1:0)
- **Vector store**: ChromaDB with persistent storage at `./chroma_db/`

### Required environment variables
Set in `~/.bashrc` (see `docs/setup.sh`):
- `CLAUDE_CODE_USE_BEDROCK=1`
- `AWS_REGION=us-east-1`
- `ANTHROPIC_MODEL=us.anthropic.claude-sonnet-4-5-20250929-v1:0`

### Activate environment
```bash
source .venv/bin/activate
```

### Verify connectivity
```bash
python test_bedrock.py  # Should return a response and token count
```

## Architecture

The system has three layers (not yet built):

1. **Ingestion** (`specs/ingestion-spec.md`)
   - Load 20 documents from `documents/`
   - One chunk per document (no splitting)
   - Extract metadata: `doc_id`, `title`, `effective_date`, `authority_tier`, `form`
   - Store in ChromaDB collection `acme_auto_corpus`

2. **Retrieval** (`specs/retrieval-spec.md`)
   - Vector search with similarity floor to detect unanswerable questions
   - Return chunks with metadata + relevance scores
   - Does NOT resolve conflicts — surfaces all candidates (e.g., both stale and current docs)

3. **Reasoning/Validation** (not yet specified)
   - Apply precedence rules to resolve conflicts
   - Detect insufficient retrieval
   - Generate responses with verification

## Critical Design Constraints

### The corpus contains deliberate traps
See `reference/CORPUS-MAP.md` for full details:

1. **Version conflict**: B3 (75% threshold, 2026) vs B4 (70% threshold, 2023)
2. **Supersession**: D4 bulletin ($45/day, 2026-05-01) overrides C3 ($30/day)
3. **Unanswerable**: Diminished value query has no corpus answer
4. **Scope conflict**: C1 vs C4 on glass deductible (both correct in different scopes)
5. **State override**: A4 (Meridian 100%) overrides B3 general rule (75%)
6. **Near-duplicate**: A1 (personal) vs A2 (fleet) — semantically similar, factually different

### Chunking is whole-document
Each of the 20 documents is a single chunk (~200 words). Do not split. Rationale: B3's closing line referencing A4 would be isolated into an irrelevant fragment if split, breaking Q7.

### Metadata extraction hazards

**effective_date parsing**:
- Four different header labels exist: `**Effective:**`, `**Last reviewed:**`, `**Date:**`, `**Effective for losses on or after:**`
- D4 has TWO dates: `**Issued:** 2026-04-15 | **Effective for losses on or after:** 2026-05-01`
- Parser MUST match on label, not position — first-date-on-line returns wrong value for D4
- D4's correct date is 2026-05-01 (the effective date for Q2, the primary build target)

**form field**:
- Derived from header: `ACME-PA-2025` → `personal`, `ACME-CF-2025` → `fleet`
- Documents with no form code default to `both`
- A1 is `personal`, A2 is `fleet` — this field separates them on Q6

**authority_tier**:
- From filename prefix: `A` → `policy`, `B` → `procedure`, `C` → `reference`, `D` → `comms`

## Build Targets

Three questions must work correctly (see `reference/QUESTIONS-AND-TRACES.md`):

- **Q2**: "How many days of rental am I covered for, and at what rate?"
  - Must return BOTH C3 and D4, then apply date-based precedence
  - Answer: 30 days, $45/day for losses on/after 2026-05-01
  - This is the primary gate — if D4 doesn't surface in retrieval, the pipeline fails

- **Q10**: Multi-document precedence (C5 overrides B2 during CAT, C4 adds glass-specific detail)

- **Q3**: "After my car is repaired, do you pay me for the lost resale value?"
  - Must detect NO relevant chunks above similarity floor
  - Correct answer: "Not addressed in available documents"
  - Tests that the system doesn't fabricate answers

## Development Commands

### Testing
```bash
# Connectivity test
python test_bedrock.py

# Ingestion verification (once built)
# Should return 20, print all filenames, populate all metadata
```

### Dependencies
```bash
pip install --upgrade pip
pip install boto3 chromadb
```

### ChromaDB operations
```python
# Collection should be recreated on re-ingestion (not appended)
# Reason: duplicate chunk IDs split scores across instances

# Delete and rebuild:
# client.delete_collection("acme_auto_corpus")
```

## File Structure

```
documents/          20 synthetic insurance docs (A1-A5, B1-B5, C1-C5, D1-D5)
reference/          Corpus map, 10 questions + traces, NOT for ingestion
  START-HERE.md     Read this first — explains the corpus design
  CORPUS-MAP.md     What each doc contains and what traps are planted
  QUESTIONS-AND-TRACES.md  Human vs agent retrieval paths
specs/              Implementation specifications
  ingestion-spec.md Chunking, metadata extraction, storage
  retrieval-spec.md Query interface, scoring, failure signals
docs/               Setup documentation
  SETUP.md          Environment setup (WSL + Bedrock + Claude Code)
  setup.sh          Automated setup script
src/                Implementation (empty — to be built)
test_bedrock.py     AWS Bedrock connectivity test
```

## Working with the Corpus

### Never ingest reference/
The `reference/` directory contains the answer key. Indexing it would let the system retrieve answers instead of reasoning to them. Only `documents/` should be ingested.

### Document count must be exactly 20
Fail loudly if not 20 — a silent 19 or 21 means a file was missed or a reference file leaked in.

### D5 is the canary
`D5-telematics-program-overview.md` is a deliberate distractor. If it appears in retrieval results for the 10 questions, retrieval is too loose (k too high or queries too vague).

## Preprocessing

Strip this HTML comment from every document before embedding (it's byte-identical across all 20 files):
```
<!-- SYNTHETIC TEST DATA. Placeholder carrier (Acme Mutual) and fictional state (Meridian). Not real insurance guidance. -->
```

Keep everything else: title, header, body.

## Score Convention

Chroma returns **distance** (lower = more similar). State clearly in docstrings whether you return raw distance or converted similarity (higher = better). Use ONE convention consistently across retrieval, run records, and thresholds.

## Retrieval Design Decisions

Three decisions marked **DECIDE** in `specs/retrieval-spec.md`:

1. **k value**: Default number of chunks to return (5 or 8?)
   - Q7 needs B3, B4, and A4 (3 docs)
   - Q10 needs C5, B2, and C4 (3 docs)
   - Higher k = more coverage but more noise for the reasoner

2. **Similarity floor**: Empirically set by running Q3 (unanswerable) vs Q2/Q10 (multi-doc)
   - Record the observed scores when setting the threshold
   - Floor goes between them, closer to Q3's end

3. **Score format**: Return Chroma's distance or convert to similarity?
   - Pick one, document it, use it everywhere

## Data Integrity Rules

From `reference/START-HERE.md`:

- If you change a number in a document → change it in `CORPUS-MAP.md` and in `QUESTIONS-AND-TRACES.md`
- Keep at least one unanswerable question (currently Q3)
- Everything is plain markdown — edit directly

## Cost Context

Running on a personal AWS account. From `docs/SETUP.md`:
- Budget: $25/month with alerts at 80% and 100%
- Synthetic data only — no real business content until migrated to company account

## Common Mistakes to Avoid

1. **Wrong D4 date**: Parsing first date on line returns 2026-04-15 (issued), not 2026-05-01 (effective)
2. **Chunking B3**: Splitting it isolates the A4 pointer into an irrelevant fragment
3. **Indexing reference/**: Answer key must never be in the vector store
4. **Appending on re-ingestion**: Creates duplicate chunk IDs and splits scores
5. **No similarity floor**: Vector search always returns something — Q3 requires detecting "no good match"
6. **Verification against stale docs**: Q2's trap — C3 passes verification but is superseded by D4

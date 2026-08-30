
## Purpose

Load the 20 corpus documents into a local Chroma collection with the metadata the
retrieval and reasoning layers need to apply precedence rules.

---

## Source

- Read from `documents/` only.
- Expect exactly **20** `.md` files.
- **Fail loudly** if the count is not 20. A silent 19 or 21 means a file was
  missed or a reference file leaked into the corpus, and every downstream result
  would be quietly wrong.
- `reference/` is never ingested. It holds the corpus map and the answer key.
  Indexing it would let the system retrieve the answer instead of reasoning to it.

---

## Chunking

**One chunk per document.** 20 documents, 20 chunks. No splitting.

Why:

- Each document is roughly 200 words, well inside the embedding input limit.
- B3's closing line ("where a state amendment specifies a different threshold,
  the state amendment governs") is the only pointer from the general total-loss
  procedure to A4. Splitting B3 would isolate that sentence into a fragment
  containing no numbers and no state name — it would rank low, never be
  retrieved, and Q7 would fail silently with a plausible answer.
- Precedence reasoning needs document-level context. A 40-word fragment does not
  carry which document, which version, or what qualifies it.

Cost accepted: retrieval is coarser. A deductible question returns all of C1,
including rows that are not needed. Acceptable at 20 documents; would not be at
2,000.

---

## Preprocessing

Strip the leading HTML comment from every file before embedding:

```
<!-- SYNTHETIC TEST DATA. Placeholder carrier (Acme Mutual) and fictional state (Meridian). Not real insurance guidance. -->
```

It is byte-identical across all 20 files, so it adds no distinguishing signal and
slightly flattens the differences the embedding is meant to capture.

Everything else — title, header line, body — is kept in the embedded text.

---

## Metadata

Five fields per chunk. All five must be populated on every chunk.

| Field | Type | Derivation |
|---|---|---|
| `doc_id` | string | Filename without extension, e.g. `B3-total-loss-valuation-procedure` |
| `title` | string | The `# ` H1 line, minus the leading hash |
| `effective_date` | ISO date string | Parsed from the header line — see below |
| `authority_tier` | string | From the group letter in the filename: `A` → `policy`, `B` → `procedure`, `C` → `reference`, `D` → `comms` |
| `form` | string | `personal`, `fleet`, or `both` — see below |

### effective_date

The header is the third or fourth line of each file. Four label variants exist:

| Label | Documents |
|---|---|
| `**Effective:**` | 17 documents |
| `**Last reviewed:**` | D1 |
| `**Date:**` | D2 |
| `**Effective for losses on or after:**` | D4 |

**Parser hazard — read this before writing the regex.** D4's header is:

```
**Issued:** 2026-04-15 | **Effective for losses on or after:** 2026-05-01
```

A regex that takes the *first* date on the line returns 2026-04-15. The correct
value is **2026-05-01**. D4 supersedes C3, and Q2 turns on that comparison, so
getting this wrong breaks the primary build target. Match on the label, not on
position.

Fallback: if no recognised label is found, log the filename and the raw header
line at WARNING and store `null`. Do not silently default to today's date or to
the file mtime — a wrong date is worse than a missing one, because a missing one
is visible.

Acceptable simplification: if the parser handles 17 and misses 3, hardcode the 3
in a small override map rather than perfecting the regex. Note it as a known
simplification in the writeup.

### form

Derived from the header line where it states one:

| Header contains | `form` |
|---|---|
| `ACME-PA-2025` only | `personal` |
| `ACME-CF-2025` only | `fleet` |
| Both codes | `both` |
| No form code (all B, C, D documents) | `both` |

A1 is `personal`, A2 is `fleet`, A3 is `personal` (attaches to the personal form
only), A4 and A5 are `both`. Everything in groups B, C and D defaults to `both`.

This field is what separates A1 from A2 on Q6, the near-duplicate trap.

---

## Storage

- `chromadb.PersistentClient(path="./chroma_db")`
- Collection name: `acme_auto_corpus`
- Chroma's default embedding function. Swappable to Bedrock Titan later; if
  changed, the collection must be deleted and re-ingested, because vectors from
  different models are not comparable.
- Chunk id: the `doc_id`.
- Re-running ingestion replaces the collection rather than appending. Appending
  would create duplicate chunks with identical ids and split retrieval scores
  across them.

---

## Interfaces

```python
def ingest(documents_path: str) -> int:
    """Load, parse, embed and store. Returns the number of chunks stored."""
```

## Done-criteria

Ingestion is complete when all of these hold:

1. `ingest("documents/")` returns **20**.
2. Every chunk has all five metadata fields populated, with no `null`
   `effective_date`.
3. Ingestion prints the 20 filenames it loaded, so a stray file is visible.



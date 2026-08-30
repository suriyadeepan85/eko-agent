# Retrieval Spec

Sample — edit it. Three decisions in here are still open and marked **DECIDE**.
They are yours to settle, and the reasoning under each is what you will defend
on Monday.

Depends on: `docs/ingestion-spec.md`. Reads the collection that spec creates.
Does not create, modify or re-embed anything.

---

## Purpose

Given a question, return the chunks most likely to contain the answer, with
enough signal attached for the reasoning and validation layers to apply
precedence rules and to detect when retrieval was insufficient.

---

## Scope

In scope: embedding the question, searching the collection, ranking, filtering,
returning chunks with scores.

Out of scope: deciding which chunk *wins* when two conflict. That is reasoning,
not retrieval. Retrieval's job is to put both candidates on the table — C3 *and*
D4, B3 *and* B4 *and* A4. Choosing between them happens downstream.

This boundary matters. If retrieval silently returns only C3, no precedence rule
downstream can save the answer, because the stale document is the only evidence
in the room.

---

## Interface

```python
def query(text: str, k: int = 5, filters: dict | None = None) -> list[dict]:
    """Return up to k chunks, ordered best first.

    Each dict contains:
      text            the chunk content
      doc_id          e.g. "D4-bulletin-2026-04-rental-limit-change"
      title
      effective_date
      authority_tier
      form
      score           relevance, see Scoring below
    """
```

`score` is returned on every chunk because US6 requires retrieval relevance
signals to be captured for the documents used in answering a query. It is not
optional and not for debugging only — it is an acceptance criterion.

---

## Scoring

Chroma returns a **distance**, where lower means more similar. That is the
opposite of the intuitive reading of a "relevance score", and mixing the two up
is an easy silent bug: a similarity floor written for one convention rejects
exactly the wrong chunks under the other.

**DECIDE:** return Chroma's raw distance, or convert to a similarity where higher
is better.

Whichever you pick, state it in the docstring and use the same convention in the
run record and in any threshold. Do not have distance in one place and similarity
in another.

---

## Default k

**DECIDE:** the default value of `k`.

The corpus has 20 chunks, so k is a large fraction of the whole collection.

- **k=5** — the default in the interface above. Tight. Risks missing a third
  relevant document on multi-document questions. Q7 needs B3, B4 *and* A4;
  Q10 needs C5, B2 *and* C4.
- **k=8** — more headroom for multi-document questions, at the cost of feeding
  more irrelevant text to the reasoner. At 20 chunks total, k=8 is 40% of the
  corpus.

Note what k interacts with: the more chunks you return, the more likely the
right one is present, and the more likely the reasoner is distracted by a
near-miss. D5 (telematics) is the deliberate distractor — if it starts appearing
in results, k is too high or the query is too vague.

---

## Similarity floor

Vector search has no concept of "no result". It returns nearest neighbours
regardless of whether anything is actually close. Ask about diminished value —
which appears nowhere in the corpus — and it will still return five chunks.

A floor is therefore required for Q3. Chunks that do not clear it are dropped;
if nothing clears it, `query` returns an empty list and the caller reports
insufficient retrieval rather than reasoning over noise.

**DECIDE:** the threshold value.

This cannot be set from first principles. Set it empirically:

1. Run the Q3 question ("after my car is repaired, do you pay me for the lost
   resale value?") and record the best score.
2. Run Q2 and Q10 and record their best scores.
3. Put the floor between them, closer to the Q3 end.

Record the observed numbers in this file when you set it. A threshold with no
recorded basis is a magic number, and future-you will not know whether it can be
changed.

---

## Filters

`filters` maps to Chroma's metadata `where` clause. Supported keys are the five
ingestion fields: `doc_id`, `title`, `effective_date`, `authority_tier`, `form`.

Not needed for the three build targets — Q2, Q10 and Q3 all work on unfiltered
search. Filtering is what Q6 needs, where A1 and A2 are near-duplicates and the
`form` field is what separates them.

**Build the parameter now, use it later.** Threading it through afterwards means
touching the reasoning layer as well.

Caution: filtering narrows *before* ranking. A wrong filter removes the correct
document entirely and the failure looks like a retrieval miss, not a filter bug.
Log the filter applied in the run record so this is visible.

---

## Failure signals

`query` reports, rather than resolves, these conditions. The caller decides what
to do; retrieval only makes them visible.

| Signal | Condition |
|---|---|
| `insufficient_retrieval` | No chunk clears the similarity floor |
| `weak_retrieval` | Best score is close to the floor |
| `filtered_empty` | A filter was applied and eliminated every candidate |

These map to US6's requirement to detect and flag insufficient or irrelevant
retrieval.

---

## Done-criteria

1. `query("rental per day limit")` returns **both C3 and D4**, each with its
   correct `effective_date` — C3 at 2025-07-01, D4 at 2026-05-01.
2. `query("how many days of rental am I covered for and at what rate")` — Q2 as
   actually phrased — also returns both. Criterion 1 uses the vocabulary of the
   documents; this one uses the vocabulary of a user, and it is the harder test.
3. `query("total loss threshold")` returns **B3, B4 and A4**.
4. The diminished value question returns **nothing above the floor**.
5. Every returned chunk carries all five metadata fields and a score.
6. D5 (telematics) does not appear in results for any of the above.

**Criterion 1 is the gate.** If D4 does not surface, Q2 is unbuildable and no
amount of agent orchestration downstream will fix it. Fix retrieval before
building anything on top — raise k, add a supersession-aware second pass, or
reconsider whether whole-document chunking is burying D4's short text.

Criterion 6 is the quiet one. D5 was put in the corpus specifically to reveal
loose retrieval. If it shows up, the problem is real even though every other
criterion passed.

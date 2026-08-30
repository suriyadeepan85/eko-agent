# Retrieval Spec


Depends on: `specs/ingestion-spec.md`. Reads the collection that spec creates.
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
opposite of the intuitive reading of a "relevance score".

**Decision:** convert distance to a similarity where higher is better, so `score`
reads intuitively and the floor is a lower bound rather than an upper one.

State this convention in the `query` docstring and apply it consistently in query
results, the run record, and the similarity floor. Distance in one place and
similarity in another is a silent bug: a floor written for one convention rejects
exactly the wrong chunks under the other.

---

## Default k

The corpus has 20 chunks, so k is a large fraction of the whole collection.

More chunks means the right one is more likely present, and the reasoner is more
likely distracted by a near-miss. D5 (telematics) is the deliberate distractor —
if it starts appearing in results, k is too high or the query is too vague.

**Decision:** k = 5. Raise it only if a done-criterion fails because a third
relevant document was cut off. Q7 needs B3, B4 and A4; Q10 needs C5, B2 and C4.
A failure there would be evidence to raise k, rather than a guess.

---

## Similarity floor

Vector search has no concept of "no result". It returns nearest neighbours
regardless of whether anything is actually close. Ask about diminished value —
which appears nowhere in the corpus — and it will still return five chunks.

A floor is therefore required for Q3. Chunks that do not clear it are dropped; if
nothing clears it, `query` returns an empty list and the caller reports
insufficient retrieval rather than reasoning over noise.

**Decision:** placeholder `0.0` (no filtering) for the first build. The threshold
cannot be reasoned to — it must be measured against this corpus and this
embedding function.

Procedure once retrieval runs:

1. Run the Q3 question ("after my car is repaired, do you pay me for the lost
   resale value?") and record the best score.
2. Run Q2 and Q10 and record their best scores.
3. Set the floor between them, closer to the Q3 end.

Record the observed scores here when the floor is set. A threshold with no
recorded basis is a magic number, and future-you will not know whether it is safe
to change.

### Observed scores

| Question | Best score | Notes |
|---|---|---|
| Q3 diminished value | | |
| Q2 rental rate | | |
| Q10 hailstorm CAT | | |

**Floor set to:** _(pending measurement)_

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

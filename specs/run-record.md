# Run Record Spec

Depends on: `specs/agent-spec.md`, `specs/retrieval-spec.md`.

One structured record per question asked. Three user stories are satisfied by this
single artifact — US3 (grounding enforcement), US4 (explainability), US6
(evaluation and failure detection). Three separate logs would drift apart; one
record read by three consumers cannot.

All decisions in this file are settled.

---

## Two constraints that govern everything below

**Assembled, never narrated.** Every field is written from what actually happened.
No LLM call reads this record and writes a summary of it. A narrated summary can
describe reasoning the system did not do, or quietly omit a rejection, and nothing
would fail — it would simply be untrue. US4 requires the explanation to align with
the final response; that alignment is only guaranteed if the explanation *is* the
record.

**Write-only from the agents' perspective.** No agent reads this back. It is a
log, not working state. What an agent needs to do its job is passed to it directly
as a parameter — the reasoner receives its rejected draft from the orchestrator in
the function call, not by reading a file.

Two reasons this matters. If agents read the record it becomes load-bearing: a
logging bug would break the system rather than just your visibility into it. And
it would reintroduce the anchoring problem the validator's statelessness was
designed to prevent — a validator that can read prior attempts is no longer blind
to them.

---

## Who writes it

**The orchestrator.** Not any agent.

Each agent returns its result; the orchestrator appends it to the record before
calling the next. No single agent sees the whole run — the validator has no idea
what the planner decided — so none could write a complete record. And five
components writing to one structure is more failure surface than it is worth.

**Written incrementally, flushed at the end.** A crash mid-run then leaves a
partial record showing how far it got, which is exactly when you most want one.

---

## Granularity

**One record per question asked**, not per agent call. A question decomposed into
two sub-questions produces one file containing both retrievals as separate
sections, the pooled chunks, and each reasoning attempt.

---

## Location

`runs/`, relative to the **project root** — not to the source file. Code launched
from inside `src/` with a relative path would write to `src/runs/`.

Filename: timestamp plus a short question slug.

`runs/` goes in `.gitignore` during development — generated output that
accumulates on every test, same treatment as `chroma_db/`. On completion, the
final evaluation runs are copied to `runs/evaluation/` and committed as a
deliverable.

**Decision — both file and console.** Write the full JSON to `runs/`, and print a
readable summary to console: the question, the plan, chunks retrieved with scores,
each attempt's verdict, and the final answer or refusal.

The file is what US6 asks for and what you compare across runs. The console
summary is what you will actually read while debugging. Doing both costs one extra
function.

---

## Structure

```json
{
  "question": "How many days of rental am I covered for, and at what rate?",
  "timestamp": "2026-08-30T14:22:10Z",

  "plan": {
    "decomposed": true,
    "sub_questions": [
      "What is the maximum number of rental days per loss?",
      "What is the per-day rental reimbursement rate?"
    ]
  },

  "retrievals": [
    {
      "sub_question": "What is the per-day rental reimbursement rate?",
      "k": 5,
      "filters": null,
      "chunks": [
        {"doc_id": "C3-rental-reimbursement-limits", "score": 0.61, "effective_date": "2025-07-01", "authority_tier": "reference"},
        {"doc_id": "D4-bulletin-2026-04-rental-limit-change", "score": 0.57, "effective_date": "2026-05-01", "authority_tier": "comms"}
      ]
    }
  ],

  "pooled_chunks": ["C3-rental-reimbursement-limits", "D4-bulletin-2026-04-rental-limit-change", "A3-endorsement-rental-coverage"],

  "attempts": [
    {
      "attempt": 1,
      "draft": "Rental is reimbursed at $30 per day for up to 30 days.",
      "claims": [
        {"claim": "$30 per day", "doc_id": "C3-rental-reimbursement-limits"}
      ],
      "verdict": "rejected",
      "reason": "C3 is superseded by D4 (2026-05-01) on the per-day rate"
    },
    {
      "attempt": 2,
      "draft": "Rental is reimbursed at $45 per day for up to 30 days, maximum $1,350 per loss.",
      "claims": [
        {"claim": "$45 per day", "doc_id": "D4-bulletin-2026-04-rental-limit-change"},
        {"claim": "up to 30 days", "doc_id": "C3-rental-reimbursement-limits"}
      ],
      "verdict": "accepted",
      "reason": null
    }
  ],

  "precedence_applied": [
    {"rule": "later_effective_date", "winner": "D4-bulletin-2026-04-rental-limit-change", "over": "C3-rental-reimbursement-limits"}
  ],

  "answer": "Rental is reimbursed at $45 per day for up to 30 days, maximum $1,350 per loss.",

  "sources": ["D4-bulletin-2026-04-rental-limit-change", "C3-rental-reimbursement-limits"],

  "failures": []
}
```

---

## Field notes

**`plan.decomposed`** — a boolean makes it visible when the planner passed a
question straight through. Without it you cannot distinguish "no decomposition
needed" from "the planner did nothing".

**`retrievals[].sub_question`** — carrying the originating sub-question is what
makes the record legible. A flat list of fifteen chunks gives no indication of
what was being looked for.

**`retrievals[].chunks[].score`** — required by US6, which asks that retrieval
relevance signals be captured for the documents used in answering. Use the
similarity convention from `specs/retrieval-spec.md` — higher is better. Do not
mix distance and similarity between this record and the retrieval layer.

**Chunk text is not stored.** Only `doc_id` and metadata. The text is retrievable
from Chroma by id, and storing it here would duplicate the corpus in every record.

**`attempts[]`** — every attempt, not just the accepted one. Two entries with the
same `reason` mean the reasoner is not using the validator's feedback, which is a
bug in the retry loop rather than a genuinely unanswerable question. With only the
final answer stored, that is invisible.

**`attempts[].claims`** — the per-claim source pairing is US3's "retrieved sources
are explicitly linked to the generated answer". It is also what the validator
needs in order to work: checking grounding means checking each claim against a
source, so the pairing has to exist regardless.

**`precedence_applied`** — which rule fired and which document won. Not required by
any story directly, but it is the difference between seeing that the answer was
$45 and seeing *why* D4 beat C3. This is the field that demonstrates reasoning
rather than retrieval.

---

## Failure types

`failures[]` holds zero or more typed entries. US6 requires detection and flagging
of insufficient retrieval, low grounding confidence, and conflicting agent
outputs.

| Type | Raised when |
|---|---|
| `insufficient_retrieval` | No chunk cleared the similarity floor |
| `weak_retrieval` | Best score close to the floor |
| `filtered_empty` | A filter eliminated every candidate |
| `low_grounding` | Validator rejected one or more claims |
| `conflicting_output` | Validator rejected the reasoner's draft — these two agents disagreed |
| `retry_exhausted` | Two attempts failed validation |
| `repeated_rejection` | Both attempts rejected for the same reason |
| `invalid_input` | Query empty, malformed, or out of scope |

`conflicting_output` and `low_grounding` will often fire together. Keep them
distinct: one describes the disagreement between agents, the other the grounding
state of the answer.

`invalid_input` covers US5's "input validation and basic safety checks", which no
question in the evaluation set otherwise exercises. Add one deliberately malformed
query to the test set.

---

## RunRecord Class Interface

**Write-only from agents' perspective** (per design constraint above), but provides
read access for UI and CLI:

**Write methods** (called by orchestrator during pipeline execution):
- `add_plan(decomposed, sub_questions)`
- `add_retrieval(sub_question, k, filters, chunks)`
- `add_pooled_chunks(doc_ids)`
- `add_attempt(attempt_num, draft, claims, verdict, reason)`
- `add_precedence(rule, winner, over)`
- `set_answer(answer)`
- `add_sources(doc_ids)`
- `add_failure(failure_type, details)`
- `flush()` — writes complete record to JSON file

**Read methods** (for UI, CLI, testing):
- `to_dict() -> dict` — returns complete record as dictionary with all trace data
- `answer` property — convenience accessor for `record['answer']`
- `print_summary()` — console output (human-readable, not for parsing)

**Usage in UI:**
```python
record = run_pipeline(question)
answer = record.answer              # Get final answer
trace = record.to_dict()            # Get complete trace for display
```

---

## Done-criteria

1. Asking one question produces exactly one JSON file in `runs/`.
2. Q2's record shows both C3 and D4 retrieved, and `precedence_applied` naming D4
   over C3.
3. Q3's record shows `retry_exhausted` and a refusal, with the retrievals that
   were attempted still visible.
4. A crash mid-run leaves a partial file rather than nothing.
5. Every score in the record uses the same convention as the retrieval layer.

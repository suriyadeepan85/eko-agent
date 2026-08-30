# Agent Spec

Depends on: `specs/ingestion-spec.md`, `specs/retrieval-spec.md`, `specs/run-record.md`.

Defines the five agent roles, the orchestrator that runs them, and the rules each
applies. All decisions in this file are settled.

---

## Components

Five roles. Three are LLM calls; two are deterministic.

| Component | LLM? | Asked for | Returns |
|---|---|---|---|
| Planner | yes | Does this question need more than one lookup? If so, what should each look up? | List of sub-questions, or the original unchanged |
| Retriever | no | Search for this text | Chunks with metadata and scores |
| Reasoner | yes | Answer this question from these chunks, applying precedence | Draft answer + per-claim source attribution |
| Validator | yes | Is each claim supported by these chunks? | Per-claim verdict + reason |
| Memory | no | What has already been asked and concluded? | Prior turns and conclusions |

The **orchestrator** is not an agent. It is plain Python: it calls the agents in
sequence, enforces the retry cap, and accumulates the run record. No LLM call, no
prompt.

---

## Why an LLM for planner, reasoner and validator

Each requires a semantic judgement that code cannot make.

- **Planner** — recognising that "how many days of rental and at what rate" is two
  questions is language understanding, not pattern matching.
- **Reasoner** — extracting that $45 applies from 2026-05-01 requires reading
  prose. A regex generalises only to phrasings anticipated in advance.
- **Validator** — judging that "the per-day maximum is $45" is supported by a
  sentence saying the maximum is *increased from $30 to $45* is paraphrase
  detection. String matching fails.

**What stays in code:** comparing two dates, counting retry attempts,
deduplicating chunks, applying the similarity floor. The LLM decides *which* rule
applies and *what the text means*; code does the comparing and counting.

---

## Memory access

| Agent | Reads memory | Why |
|---|---|---|
| Planner | **yes** | "What if a CAT is active?" is not a searchable question — it is a modification of the previous one. Without memory the planner searches for catastrophe rules and loses that the user was asking about contact timing. |
| Reasoner | **yes** | Avoids re-deriving established facts and keeps answers consistent across turns. |
| Validator | **no** | Deliberate. |

**The validator is stateless by design.** It sees only the current draft and the
current chunks. Given the same draft and chunks it must return the same verdict
every time.

If it could see prior turns, it might accept on precedent rather than evidence.
If it could see the attempt count, it might soften on attempt three — weakening
the grounding check exactly when the answer is most doubtful. Planner and reasoner
are generative, so prior context shapes what makes sense. The validator is
judicial: it evaluates a fixed artifact against fixed evidence.

Memory is a **separate store**, not owned by any agent. At this scale it is
deterministic — question history and conclusions reached, with a read and a write.
No LLM call, no judgement.

**Build order:** the planner and reasoner take a `context` parameter from the
start, even when it is empty. Memory is wired in after the pipeline works
end-to-end on a single-turn question. Adding it later then changes what is passed,
not the agents' signatures.

---

## Retrieval per sub-question

One `query()` call per sub-question, `k=5`.

- Results are **pooled** before reaching the reasoner. Q10's answer needs the CAT
  threshold from one sub-question and normal timelines from another, held
  together at once.
- **Deduplicate by `doc_id`**, keeping the higher score. C5 may be returned for
  two sub-questions; without dedup the reasoner sees it twice and may weight it as
  two pieces of evidence.
- **Which sub-question produced each chunk travels with it.** Nearly free, it
  helps the reasoner see why each chunk is present, and it makes the run record
  legible. Without it the reasoner receives a flat list with no indication of what
  was being looked for.

**Volume caution.** Three sub-questions at k=5 is 15 chunks before dedup —
most of a 20-document corpus. Watch this on the first Q10 run. If the pooled set
approaches the whole corpus, retrieval has stopped narrowing anything.

---

## Precedence rules

The reasoner applies these when documents conflict. The LLM decides which rule
applies; the comparison itself is code where possible.

1. **Later effective date wins.** D4 (2026-05-01) supersedes C3 (2025-07-01) on
   the rental rate. B3 (2026-01-01) supersedes B4 (2023-03-01) on the total loss
   threshold.
2. **More specific beats general.** A4's Meridian amendment overrides B3's general
   threshold for Meridian risks. C4's repair-only glass waiver is an exception to
   C1's general rule, not a contradiction of it.
3. **Procedure beats customer-facing.** B2's one-business-day contact standard is
   authoritative over D1's FAQ wording of "24 hours".

Rule 3 maps to the `authority_tier` metadata field: `policy` > `procedure` >
`reference` > `comms`.

Where two documents govern **different actors** rather than conflicting, neither
wins — the correct answer states the distinction. The TPA-style case: an external
limit and an internal tier are not in conflict, they apply to different parties.

---

## Retry loop

1. Reasoner produces a draft with per-claim sources.
2. Validator returns a verdict per claim.
3. On rejection, the orchestrator returns **the rejected draft and the reason** to
   the reasoner. The reasoner needs this history or attempt two repeats attempt
   one. The validator never receives it.
4. **Maximum two attempts.** The orchestrator counts; the validator does not know
   which attempt it is judging.
5. On exhaustion — see DECIDE below.

**Log whether both rejections cited the same reason.** The same reason twice means
the reasoner is not using the feedback — a bug in the retry loop, not a genuinely
unanswerable question. This is distinct from a real refusal and must be
distinguishable in the run record.

**Decision — refuse, informatively.**

Return no answer. State that grounding could not be established, name what was
searched, and list which documents were retrieved. A bare refusal is useless; an
informative one tells the user three actionable things — that the question was not
answered, what was looked for, and where the gap is.

Shape of the refusal:

> I could not find support for this in the available documents. I searched for
> "diminished value" and "post-repair value loss", and retrieved the personal auto
> policy summary, the repair network rules, and the glass claim handling
> reference. None of them address payment for lost resale value after repair.

The alternatives shift the burden onto the user. A draft with a warning attached
asks them to judge whether an answer the system already flagged as ungrounded is
safe to act on, and most readers skim the warning — in a claims context that is
how a wrong number gets acted on. Returning only the grounded claims is worse: a
partial answer reads as complete, with no signal that anything was dropped.

This path is also how **Q3 fires**. Diminished value is absent from the corpus,
the reasoner will draft something regardless, the validator will find no
supporting chunk, and two attempts later the system lands here. The similarity
floor does not catch Q3 — see `specs/retrieval-spec.md`. So this is not an edge
case; it is the visible output of hallucination control.

---

## Output

The answer shown to the user is **the reasoner's accepted draft, unmodified.**

- On acceptance the validator produces no user-facing text. Its per-claim support
  record becomes source attribution and goes in the run record.
- On refusal the validator's reason is what the user sees, formatted by the
  orchestrator — data, not prose the validator wrote.

**No fourth LLM call to polish the answer.** A formatting pass would mean the
validated text and the displayed text are different texts, and the grounding
guarantee stops applying to what the user actually reads. If drafts read badly,
fix the reasoner's prompt — do not add a rewriting stage.

The same principle governs the explanation: it is **assembled from the run
record**, never narrated by a separate model call. A narrated summary can describe
reasoning the system did not do, or omit a rejection, and nothing would fail. It
would simply be untrue. This is US4's alignment criterion.

---

## Scoped out

**Improvement 1 — retrieve-then-plan-then-retrieve.** A cheap first retrieval on
the raw question, so the planner decomposes knowing what the corpus actually
contains rather than guessing. Better architecture: as written, the planner may
split a question three ways when the corpus addresses two, or miss that a
superseding bulletin exists. Scoped out for time; plan-first is sufficient for Q2,
Q10 and Q3.

**Improvement 2 — LLM-based memory.** Summarising history, selecting what is
relevant, compressing older turns. That selection problem only appears when
history exceeds the context window, which does not happen at two-turn scale. The
deterministic store is honest for this build.

---

## Done-criteria

1. **Q2** — "how many days of rental am I covered for, and at what rate?" returns
   **$45/day, 30 days, $1,350 max**, citing D4. Not $30 from C3. This is the
   supersession target.
2. **Q10** — "a hailstorm damaged 200 cars in one county, how does that change
   handling?" concludes **200 is below the 250 threshold, so no CAT is declared**
   and normal B2 timelines apply. This requires arithmetic on a retrieved number;
   no chunk contains the answer.
3. **Q3** — the diminished value question **refuses**, and the refusal names what
   was searched.
4. Every run writes a complete record to `runs/` per `specs/run-record.md`.
5. Agent invocation order is visible in the record — US2 requires traceable
   interactions.

Criterion 1 is the gate. Retrieval already surfaces both C3 and D4, so a $30
answer means the precedence rule is not firing, not that retrieval failed.

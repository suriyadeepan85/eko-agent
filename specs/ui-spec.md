# UI Spec

Depends on: `specs/agent-spec.md`, `specs/run-record.md`.
Paired with: `specs/deployment-spec.md` for hosting.

Optional. The case study puts frontend out of scope, and the CLI already satisfies
US6's "console logs, files, or UI view". Build this only after the evaluation runs
and the README are complete.

---

## Purpose

Make the multi-agent coordination visible in one view.

The brief asks for a system that moves beyond a single chatbot. A chat interface
would show an answer in a bubble and hide everything that distinguishes this system
from single-pass RAG — the plan, the retrieval scores, the attempts, the precedence
rule that fired. The interesting output is the trace, so the page is built around
displaying it.

**This is display work, not logic.** Every field shown already exists in the run
record. The UI reads what the orchestrator produces and lays it out. It contains no
reasoning, no retrieval, and no decisions.

---

## Not a chat interface

Deliberate, for two reasons.

**Memory is a stub.** Per `specs/agent-spec.md`, `get_context()` returns an empty
list, `add_turn()` is a no-op, and the `context` parameter never reaches either
prompt. The system is single-turn only. A chat interface would put the least-built
component at the front.

**Chat hides the architecture.** There is nowhere natural in a message bubble for a
plan, five retrieval scores with effective dates, per-claim attribution, and a
precedence entry. A page has room for all of it.

### Structured so chat is additive

Two choices now make multi-turn a later addition rather than a rewrite:

1. **Render from a run record, not from arguments.** One function takes a run record
   and displays answer plus trace. Single-question mode calls it on the page; chat
   mode would call the same function inside a message bubble. One renderer, two
   layouts.
2. **Do not work around the missing context parameter.** `run_pipeline(question,
   project_root)` does not currently expose context. Leave that alone rather than
   building a UI-side workaround — when memory is implemented, the parameter is
   added once, in one place.

---

## Technology

**Streamlit.** No server to run, no frontend build, no additional dependencies
beyond `pip install streamlit`. Launched with `streamlit run app.py`.

Entry point: `app.py` at the project root. It calls `run_pipeline()` from
`src.agents` — the same function the CLI uses. No parallel code path.

**Implementation note:** `run_pipeline()` returns a `RunRecord` object (not a string).
Access the answer via `record.answer` and trace data via `record.to_dict()`. This
allows the UI to render the complete trace without reading JSON files from disk.

---

## Corpus loading

**Automatic on first load**, with visible confirmation. A reviewer lands on a working
app rather than one that first asks them to press something whose purpose is unclear.

Behaviour:

1. On startup, check whether collection `acme_auto_corpus` contains 20 chunks.
2. If not, run ingestion from `documents/` with a spinner.
3. Display a status panel: **"Corpus loaded: 20 documents"**, with expandable
   document viewers (each filename expands to show full document content) and a
   **Re-ingest** button.
4. Question input is disabled until the corpus is confirmed loaded. Asking a
   question against an empty collection returns nothing useful and reads as a
   broken system.

The status panel is not decoration. It makes an architectural step visible that a
reviewer would otherwise never see, which is part of why this page exists.

### Guarding against repeated ingestion

**Streamlit reruns the entire script on every interaction** — not only on refresh.
Typing a question, pressing a button, expanding a panel all re-execute the file top
to bottom. Unguarded ingestion would fire every time.

Two guards, both required:

- **Check the collection count** before ingesting. This survives everything — reruns,
  refreshes, new browser sessions — because it checks actual state rather than
  remembering.
- **`st.cache_resource`** for the Chroma client and the ingestion call. Runs once per
  app process.

**Do not use `st.session_state` for this.** It is per-user-session, so two reviewers
would each trigger ingestion. The collection is shared app state, not session state.

When hosted, the container is ephemeral and restarts on idle, so ingestion runs again
after a restart. Unavoidable, and acceptable at a few seconds for 20 documents. The
count check handles it with no special casing.

---

## Layout

Single page, top to bottom.

**1. Corpus status** — as above. Collapsed to a single line once loaded.

**2. Question input**
- Text input, full width (Streamlit auto-submits on Enter/blur, no separate Ask button needed)
- Below it, the three build-target questions as one-click example buttons (vertical layout,
  full question text shown), so a reviewer who does not know the corpus can see the system
  work immediately:
  - "How many days of rental am I covered for and at what rate?"
  - "A hailstorm damaged 200 cars in one county. How does that change handling?"
  - "After my car is repaired, do you pay me for the lost resale value?"

**3. Question** — Display the question that was asked (from `record.to_dict()['question']`)

**4. Answer**
- The reasoner's accepted draft, unmodified. Per `specs/agent-spec.md` there is no
  formatting pass — the UI does not rewrite, summarise, or restyle the answer text.
- On refusal, the refusal message with the same prominence. A refusal is a result,
  not an error state, and must not be styled as a failure.

**5. Sources** — the documents cited, by `doc_id` and title.

**6. Trace** — the section that justifies the page existing.

Expandable panels, collapsed by default except Plan and Precedence:

| Panel | Contents |
|---|---|
| Plan | `decomposed` true/false, and the sub-questions |
| Retrievals | One group per sub-question. Each chunk: `doc_id`, score, `effective_date`, `authority_tier` |
| Attempts | Each attempt: draft, verdict, and reason on rejection |
| Precedence | Which rule fired, which document won, over which |
| Failures | Typed entries from `failures[]`, or "none detected" |

**Precedence expanded by default.** It is the field that shows reasoning rather than
retrieval, and it is what distinguishes this system's output from the baseline's.

---

## Display rules

**Scores use the similarity convention** from `specs/retrieval-spec.md` — higher is
better. Do not display raw Chroma distances. Do not convert twice.

**Show the similarity floor alongside the scores** (currently 0.44). A score of 0.46
means nothing without it. Chunks close to the floor are the ones worth noticing —
D5, the deliberate distractor, has surfaced at 0.4556 in a real run.

**Do not colour-code answers by confidence.** The system has no confidence score, and
inventing a visual one would imply a signal that does not exist.

**Empty `failures[]` displays as "none detected", not as a blank.** An empty panel
reads as broken; an explicit "none" reads as checked.

---

## What the UI must not do

- **No LLM call of its own.** No summarising the trace, no rephrasing the answer, no
  generating an explanation. The explanation is assembled from the run record — a
  narrated summary can describe reasoning the system did not do and nothing would
  fail. This is US4's alignment criterion, and the UI is the easiest place to break it.
- **No re-running or retrying** from the interface. One question, one pipeline run.
- **No editing the corpus** or uploading documents — see Known limitations.
- **No caching answers across questions.** Each run is independent, as the CLI's are.

---

## Run records

The UI does not bypass record-writing. `run_pipeline()` writes to `runs/` exactly as
it does from the CLI, and the UI reads the returned record to render the trace. A
question asked through the UI is indistinguishable in `runs/` from one asked at the
command line.

When hosted, `runs/` is on an ephemeral filesystem and is lost on container restart.
This is acceptable: the committed records in `evidence/` are the durable artifact.

---

## Known limitations

**No document upload.** The pipeline is corpus-agnostic but ingestion is not.
`authority_tier` is derived from the filename's group letter, `effective_date`
matches four label variants found in this corpus, `form` looks for `ACME-PA-2025`,
and whole-document chunking assumes roughly 200-word files. Upload arbitrary
documents and those fields come back empty, precedence cannot fire, and the system
silently degrades to baseline behaviour while still producing plausible answers.

That failure mode is worse than the missing feature — a reviewer would upload a file,
get a reasonable answer, and conclude the precedence machinery generalises. It does
not. Generalising would require metadata extraction driven by document content rather
than filename convention, plus chunk-size handling for longer documents.

**Requires AWS credentials to run locally.** A reviewer without Bedrock access cannot
run this. See `specs/deployment-spec.md` for the hosted option, and `evidence/` for
committed run records that need no credentials at all.

---

## Scoped out

**Multi-turn chat.** Requires implementing the two memory stubs, adding context to the
planner and reasoner prompts, exposing context through `run_pipeline`, and session
state in the UI. The renderer and the untouched pipeline signature make this additive.

**Corpus browser.** Viewing the 20 documents in the UI. They are in the repository and
readable there.

**Comparison view.** Running the same question through `src/baseline.py` and the full
pipeline side by side. Genuinely the most compelling demonstration of what the agents
add — the baseline answered Q2 with $45 by inference, the pipeline answers $45 by rule
and records that D4 beat C3 on effective date. Scoped out for time, not for value.

---

## Done-criteria

1. `streamlit run app.py` starts without error.
2. On first load, the corpus ingests automatically and the status shows "Corpus
   loaded: 20 documents". Question input is disabled until then.
3. Interacting with the page — typing, expanding a panel, pressing a button — does
   not re-trigger ingestion.
4. Asking Q2 shows the answer, and the Precedence panel names D4 over C3.
5. Asking Q3 shows the refusal with the same prominence as an answer, not as an error.
6. Every score displayed matches the corresponding value in the run record file.
7. A question asked through the UI produces a record in `runs/` identical in shape to
   one asked from the CLI.

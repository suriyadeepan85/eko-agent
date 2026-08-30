Seven changes to app.py. Copy, layout and one small interaction. Do not alter
pipeline behaviour, trace rendering logic, the password gate, or the session cap.

Keep the single-column stacked layout — do not move the corpus to a sidebar. The
trace section needs full width, and the corpus is context a reviewer reads once
rather than a companion panel.

---

**1. Page title**

Change to: `Enterprise Knowledge Operations Agent`

Remove "Acme" and "Insurance Policy" entirely. The current title reads like a real
carrier's product and undersells what the system is.

---

**2. Description below the title**

Add three short lines:

> A multi-agent system that answers questions by reasoning across a document corpus —
> planning, retrieval, reasoning and validation are handled by separate agents.
>
> The corpus is fabricated test data for a fictional carrier. It is not real insurance
> guidance.
>
> Every answer includes the full reasoning trace: the plan, retrieved documents with
> relevance scores, validation verdicts, and which document won when sources conflicted.

The third line matters most — a reviewer has no way to know the trace exists until a
question returns, and the trace is the point of the page.

---

**3. Corpus section**

Expand by default. Currently collapsed, so a reviewer never sees that ingestion
happened or what the system reasons over.

Header:

> **Corpus used by this app — 20 synthetic documents**

Inside the panel, above the file list:

> Fabricated auto insurance documents for a fictional carrier: policy forms, claims
> procedures, reference schedules, and internal communications.

---

**4. Question input label**

Change from `Ask a question about your policy:` to:

> `Ask a question about the corpus:`

It is not the reviewer's policy — it is a fictional carrier's document set, and the
current wording sets the wrong expectation.

---

**5. Example question labels**

The three example buttons currently show the raw question text only. Add a short
prefix to each so a reviewer understands what is being demonstrated:

- `Conflicting sources —` How many days of rental am I covered for and at what rate?
- `Reasoning over retrieval —` A hailstorm damaged 200 cars in one county. How does that change handling?
- `Refusal —` After my car is repaired, do you pay me for the lost resale value?

Without this, all three look like ordinary questions and the reviewer has no reason to
notice that each exercises a different capability.

---

**6. Sidebar wording**

The sidebar currently says the 30-question cap "prevents unbounded spend". Reword to
state the limit without drawing attention to billing:

> Hosted demo. Limited to 30 questions per session — click "Exit Session" to reset.

---

**7. Expandable sources**

In the Sources section, make each cited document expandable to show its full text
inline, so a reviewer can check a citation without scrolling back to the corpus panel.

This is what a reviewer actually wants when the answer says D4 beat C3 — to read D4.
It gives the cross-referencing benefit without the layout cost of a side panel.

Read the document text from `documents/`, not from the vector store, so what is shown
is the source file rather than the processed chunk.

---

Do not change anything else.

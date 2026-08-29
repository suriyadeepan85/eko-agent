# Start Here

Three files and a folder. No code yet — this is still the "one plus one without programming" stage.

```
START-HERE.md            ← you are here
CORPUS-MAP.md            ← what each document contains and what is planted in it
QUESTIONS-AND-TRACES.md  ← 10 questions, human path vs agent path, side by side
corpus/                  ← 20 documents, plain markdown, ~200 words each
```

## Do this in order

**1. Read the corpus. About 25 minutes.**
Read all 20 documents straight through, no notes. You are building the mental model that lets you grade answers later. Do not skip this — it is the whole reason we chose synthetic data over a public dataset.

**2. Fill in the map. About 20 minutes.**
Open `CORPUS-MAP.md`. For each row, write one line in the last column in your own words: what this document says and what you noticed about it. Where my "deliberately planted" note is wrong or unclear, fix it.

At the end of this step the map is yours. That was the concern you raised — that you cannot own data you did not write. The map is the answer.

**3. Answer the ten questions by hand. About 45 minutes.**
Open `QUESTIONS-AND-TRACES.md`. Cover the answer key. Answer each question from the documents alone, writing down which documents you opened and in what order.

Then compare against my key. Two things to watch for:

- Where you disagree with my answer, **you are probably right** — you know insurance and I invented this carrier. Change the key.
- Where you reached the right answer but by a path I did not describe, write that path down. It is a requirement I missed.

**4. Only then, build.**
Your hand-written paths from step 3 become the agent design. Every instinct you used without noticing — checking a date, ranking procedure above FAQ, comparing 200 to 250 — is a step, a rule, or a metadata field. Nothing in the pipeline gets it for free.

## Tweaking

Everything is plain markdown. Edit directly. Two rules:

- Change a number in a document → change it in the map and in the answer key. Three places, always. A map that has drifted from the corpus is worse than no map.
- Keep at least one unanswerable question. It is the cheapest possible test of whether your system will fabricate.

## Sizing note

Twenty documents is right for learning and small for a demo. If the case study needs more volume, add documents to Group C — reference tables are easy to multiply without creating traps you have to track. Keep the trap count where it is. Six is plenty to debug.

## What this is not

Fabricated content, placeholder carrier name, fictional state. It exists to make retrieval fail in ways you can see. Do not reuse any of it as insurance guidance.

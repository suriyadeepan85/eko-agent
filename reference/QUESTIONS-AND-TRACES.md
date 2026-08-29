# 10 Questions — Human Retrieval vs Agentic Retrieval

For each question: the answer you expect, how a knowledgeable human gets there, how the agent pipeline gets there, and **the gap** — the thing the human does for free that the agent needs told explicitly.

The answer key is a draft. Read it, argue with it, change it. You decide what correct means here.

Agent roles used throughout: **\[S]** search, **\[R]** reason/draft, **\[V]** verify, **\[P]** publish.

\---

## Q1. "My car was totaled. How much do I get?"

**Trap:** version conflict (B3 vs B4)
**Expected:** ACV at time of loss, less deductible, using the **75%** threshold from B3 v4.0. B4 is from 2023 and superseded.

```
HUMAN                                  AGENTIC
question                               question
  ↓                                      ↓
"totaled" → total loss valuation       \[S] embed → nearest chunks
  ↓                                      ↓ returns B3, B4, C1, A1
pulls the valuation doc                  ↓
  ↓                                    \[R] reads all four
sees TWO versions                        ↓ sees 75% and 70%, no basis to choose
  ↓                                      ↓
checks effective dates                 \[V] flags contradiction
  ↓ 2026 beats 2023                      ↓ re-searches, still two docs
uses 75%, subtracts deductible           ↓
  ↓                                    \[P] answers, or asks for help
answers with the doc version
```

**The gap:** you compared dates without being asked. To the embedder, both documents are equally relevant — they are nearly identical text. Recency has to become an explicit field on each chunk and a rule the verify step applies.

\---

## Q2. "How many days of rental am I covered for, and at what rate?"

**Trap:** supersession (D4 over C3)
**Expected:** 30 days; **$45/day** for losses on/after 2026-05-01, $30/day before. Max $1,350.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
"rental" → limits schedule C3          \[S] → C3, A3, D4?  (maybe)
  ↓                                      ↓
reads $30/day                          \[R] reads C3, drafts "$30/day"
  ↓                                      ↓
remembers the bulletin                 \[V] checks claim against C3 — it matches!
  ↓                                      ↓ verification PASSES on a wrong answer
checks date of loss                      ↓
  ↓                                    \[P] publishes $30/day
answers $45 with the bulletin
```

**The gap:** the dangerous one. Verification against retrieved text cannot catch an error when the retrieved text is itself stale. The human's "I remember a bulletin" has no equivalent. You need bulletins linked to what they supersede, or a search step that always asks "is there a later document about this topic?"

\---

## Q3. "After my car is repaired, do you pay me for the lost resale value?"

**Trap:** unanswerable
**Expected:**the corpus does not address diminished value. Correct answer is to say so — no document supports either a payment or a denial.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
searches for diminished value          \[S] embeds → returns SOMETHING
  ↓                                      ↓ (nearest chunks are always returned)
finds nothing                            ↓ A1 covered vehicles, A5 exclusions
  ↓                                      ↓
says "not covered here, ask            \[R] sees "private passenger car, pickup, van"
 underwriting"                           ↓ infers motorcycle is excluded — plausible, unsupported
                                         ↓
                                       \[V] is the inference IN the chunks? No.
                                         ↓ should reject
                                       \[P] "not addressed in available documents"
```

**The gap:** vector search has no concept of "no result." It returns the nearest neighbours regardless of whether they are close. You need a similarity floor, and a verify rule that rejects any claim not literally supported.

\---

## Q4. "Do I pay a deductible for a cracked windshield?"

**Trap:** scope conflict (C1 vs C4)
**Expected:** repair → deductible waived. Replacement → full comprehensive deductible. Both docs are correct in their own scope.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
knows glass sits under comprehensive   \[S] → C1, C4, A1
  ↓                                      ↓
reads C1: comp deductible applies      \[R] two statements that look contradictory
  ↓                                      ↓ picks one, or hedges badly
reads C4: waived if repaired             ↓
  ↓                                    \[V] flags conflict
sees these aren't in conflict —          ↓ cannot tell scope from generality
 one is the general rule                 ↓
  ↓                                    \[P] risk: "sources disagree"
asks: repair or replace?
```

**The gap:** you resolved it by recognising general rule vs exception. Nothing in the text marks which is which. Either the chunks carry that metadata, or the reasoning agent is instructed to prefer the more specific document.

\---

## Q5. "When will an adjuster contact me?"

**Trap:** FAQ vs procedure vs CAT (D1, B2, C5)
**Expected:** one business day normally; four hours if non-drivable; **five business days** during an active CAT. D1's "24 hours" is loose customer wording, not the standard.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
knows to ask: is a CAT active?         \[S] → D1, B2, C5
  ↓                                      ↓
checks the file's CAT code             \[R] three different timeframes
  ↓                                      ↓ no access to whether a CAT is active
knows FAQ is marketing, procedure         ↓
 is authority                          \[V] flags conflict between 24h and 1 business day
  ↓                                      ↓
answers conditionally                  \[P] must answer conditionally, or ask
```

**The gap:** two things. Source authority — the human ranks procedure above FAQ instinctively; and **state** — "is a CAT active" is not in any document, it is a fact about right now. Some questions cannot be answered from a corpus alone.

\---

## Q6. "My company van was hit. Which policy applies and what's the limit?"

**Trap:** near-duplicate (A1 vs A2)
**Expected:** commercial fleet form A2. $1,000,000 combined single limit, not 100/300/50. Downtime reimbursement, not rental.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
"company van" → business → fleet       \[S] → A1 and A2 both score high
  ↓                                      ↓ (nearly identical vocabulary)
goes straight to A2                    \[R] may blend both, or pick A1
  ↓                                      ↓ produces 100/300/50 — wrong form
notes fleet has no rental endorsement    ↓
  ↓                                    \[V] the limit IS in a retrieved chunk
answers $1M CSL + downtime               ↓ verification passes on the wrong doc
                                       \[P] confidently wrong
```

**The gap:** one word — "company" — decided the whole answer for you. Embeddings weight it barely at all. This is why chunks need document-level metadata (form type, applies-to) that the search step can filter on, not just similarity.

\---

## Q7. "The car is garaged in Meridian and it's a total loss. Same threshold?"

**Trap:** state override (A4 over B3)
**Expected:** no — **100%** in Meridian, not 75%. Settlement must also include sales tax and title fees.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
"Meridian" → check state amendment     \[S] → B3, A4, B4
  ↓                                      ↓
reads A4: 100% threshold               \[R] must apply precedence: state beats general
  ↓                                      ↓ B3's last line does say this — if that chunk survived
applies precedence automatically         ↓
  ↓                                    \[V] checks 100% is supported → yes, in A4
also catches tax/fees requirement         ↓
  ↓                                    \[P] may miss the tax/fees part entirely
full answer
```

**The gap:** two-hop reasoning. The answer requires knowing A4 exists *and* that it wins. Note the fragility: B3's signpost line ("where a state amendment specifies...") might be in a chunk that never gets retrieved. Chunk boundaries silently destroy this.

\---

## Q8. "Can I use my own repair shop?"

**Trap:** mild — completeness, not conflict
**Expected:** yes, any licensed shop. But non-network means carrier-written estimate, prevailing labor rates, and any excess is yours.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
reads C2                               \[S] → C2, D1
  ↓                                      ↓
answers yes, AND explains the          \[R] "Yes, you can use any shop"
 consequences                            ↓ technically correct, materially incomplete
  ↓                                    \[V] every claim supported → PASSES
knows the question behind the             ↓
 question                              \[P] publishes a thin answer
```

**The gap:** verification checks that nothing is *wrong*. It does not check that nothing is *missing*. That is a separate test, and it is much harder to automate. Good baseline question — everything passes and the answer is still weak.

\---

## Q9. "My claim was flagged for fraud. What happens, and who decides?"

**Trap:** multi-hop (D2 + D3)
**Expected:** routes to Complex, senior field adjuster, payment authority suspended. Only the SIU manager clears the flag; denial needs Claims Executive sign-off. Initial disposition in 15 business days.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
D2 for what flagging does              \[S] → D2 (strong), D3 (weaker), B2
  ↓                                      ↓
D3 for the authority chain             \[R] answers from D2 alone
  ↓                                      ↓ "who decides" partly answered
knows one question has two parts         ↓
  ↓                                    \[V] supported → passes
stitches both                            ↓
                                       \[P] half the question answered
```

**The gap:** you decomposed "what happens / who decides" into two searches. A single embedding of the whole question lands between the two documents and may retrieve neither well. Multi-part questions need a planning step that splits them before searching.

\---

## Q10. "A hailstorm damaged 200 cars in one county. How does that change handling?"

**Trap:** synthesis across C5 + B2 + C4 + C1
**Expected:** 200 is **below** the 250-claim CAT threshold, so no CAT declaration and normal B2 timelines apply. If it were declared: 5-day contact, photo estimating, hail under $5,000 settled without inspection, supplements to $3,000.

```
HUMAN                                  AGENTIC
  ↓                                      ↓
reads C5: threshold is 250             \[S] → C5, B2, C4
  ↓                                      ↓
compares 200 to 250                    \[R] retrieves CAT rules, describes them
  ↓                                      ↓ never performs the comparison
concludes: not a CAT                     ↓ answers as if CAT applies — wrong
  ↓                                    \[V] the 5-day figure IS in C5 → passes
answers with normal timelines,           ↓
 notes what would change at 250        \[P] confidently wrong again
```

**The gap:** the answer requires **arithmetic on a retrieved number**, not retrieval of the answer. No chunk contains "200 is less than 250." Retrieval-only pipelines fail this class silently, and verification cannot catch it because every quoted figure is real.

\---

## What the ten questions collectively prove

|Failure mode|Questions|Why retrieval alone cannot fix it|
|-|-|-|
|Recency / versioning|Q1, Q2|Both versions are equally similar to the query|
|No-answer detection|Q3|Nearest-neighbour search always returns something|
|Precedence and scope|Q4, Q7|Text does not mark which rule wins|
|Source authority|Q5|FAQ and procedure look equally relevant|
|Wrong-but-supported|Q6, Q10|Verification passes because the quote is real|
|Completeness|Q8|Verification tests correctness, not sufficiency|
|Decomposition|Q9|One embedding for a two-part question lands nowhere|

Run these before you build anything. Answer all ten yourself from the documents, by hand, in one sitting. Whatever you did in your head to get each answer is the specification for what your agents must be told to do.


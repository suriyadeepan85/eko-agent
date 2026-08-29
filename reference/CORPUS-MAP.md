# Corpus Map

**This file is yours.** I drafted it; you own it. Read each document, then edit the "What I checked" column in your own words. That is what makes you the owner of data you did not type.

All content is fabricated. Placeholder carrier: **Acme Mutual** — deliberately a stock placeholder name, not a real company. Fictional state: **Meridian**. Nothing here is real insurance guidance — the fiction is deliberate, so you never confuse test data with the real thing.

\---

## Group A — Policy documents

|File|What it covers|Deliberately planted|What I checked|
|-|-|-|-|
|A1 personal auto policy summary|Coverage parts, ACV settlement basis, 100/300/50 limits|Says rental is **not** in base form — must come from endorsement||
|A2 commercial fleet policy|Fleet coverage, $1M CSL, downtime reimbursement $75/day|Looks very similar to A1 in embedding space — retrieval bait||
|A3 rental reimbursement endorsement|What triggers rental, what is excluded|Points to the limits schedule but states no numbers||
|A4 Meridian state amendment|Total loss threshold **100%**, appraisal rights, tax/fees|**Overrides** B3's threshold for Meridian risks||
|A5 exclusions list|Physical damage exclusions|Says nothing about motorcycles — see Q3||

## Group B — Claims procedure

|File|What it covers|Deliberately planted|What I checked|
|-|-|-|-|
|B1 FNOL intake|Required fields, drivability flag|Says assignment is *not* handled at intake||
|B2 adjuster assignment|Segments, contact standards (1 business day)|Ends by saying CAT rules replace these — easy to miss||
|B3 total loss valuation v4.0 (2026-01-01)|Threshold **75%**, 90-day/100-mile comps|Current version||
|B4 total loss valuation v3.2 (2023-03-01)|Threshold **70%**, 180-day/150-mile comps|**Superseded, but does not say so.** Only the date tells you||
|B5 subrogation checklist|Referral triggers, deductible recovery|Low-conflict filler||

## Group C — Reference data

|File|What it covers|Deliberately planted|What I checked|
|-|-|-|-|
|C1 deductible schedule|Options per coverage, fleet defaults|Says glass takes comprehensive deductible, **no waiver mentioned**||
|C2 DRP repair network rules|Choice of shop, network vs non-network|Mild conflict with D1's simplified FAQ answer||
|C3 rental limits schedule|**$30/day**, 30 days, $900 max|**Stale.** D4 changed it. C3 contains no pointer to D4||
|C4 glass claim handling|Repair vs replace, deductible waived on repair-only|**Partial conflict with C1** — waiver applies only to repairs||
|C5 catastrophe surge rules|CAT declaration, 5-day contact standard|Overrides B2 while active||

## Group D — Comms and edge cases

|File|What it covers|Deliberately planted|What I checked|
|-|-|-|-|
|D1 customer FAQ|Plain-language answers|**Says 24 hours** for adjuster contact; B2 says one business day. Not the same thing||
|D2 fraud flag memo|Indicators, what flagging does, authority|Multi-hop with D3 on who decides||
|D3 escalation matrix|Who escalates what, final authority|Points valuation disputes to state appraisal process (A4)||
|D4 bulletin 2026-04|Rental **$45/day** from 2026-05-01|**Supersedes C3.** Says "until then, this bulletin controls"||
|D5 telematics overview|DriveSense program|**Distractor.** No question touches it. If it shows up in results, retrieval is loose||

\---

## The six planted traps

1. **Version conflict** — B3 (75%) vs B4 (70%). Only the effective date distinguishes them.
2. **Supersession** — D4 bulletin overrides C3's $30/day. The stale doc looks authoritative.
3. **Unanswerable** — diminished value appears nowhere. The correct answer is "not in the corpus," not a guess.
4. **Scope conflict** — C1 vs C4 on glass deductible. Both true, in different scopes.
5. **State override** — A4 beats B3 for Meridian risks. Requires reading two docs and applying precedence.
6. **Near-duplicate** — A1 vs A2. Semantically close, factually different, and picking wrong changes the answer entirely.

\---

## How to tweak

* **Too easy?** Delete the "State variation" line at the bottom of B3 so nothing signposts A4.
* **Too hard?** Add `\*\*SUPERSEDED\*\*` to B4's title.
* **Add a trap:** duplicate C2 with a different labor-rate rule and no date.
* **Change domain:** the structure (policy / procedure / reference / comms) transfers to health or property unchanged.

Edit the documents directly. They are plain markdown. If you change a number, change it in this map too, or the map stops being trustworthy — and the map is the thing you debug against.


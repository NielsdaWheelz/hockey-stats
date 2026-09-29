# HockeyViz — Shift Starts and Ends, Part 2

- **Title (as published):** "Shift Starts and Ends, Part 2" (page `<title>`: "Shots In Shifts Part 2")
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Article date:** September 3, 2015
- **URL used:** https://hockeyviz.com/txt/shifts2 — fetched directly via curl with a browser User-Agent (WebFetch returns HTTP 403 from hockeyviz.com). Full HTML retrieved (≈95 KB; no subscriber gate on the body).
- **Accessed:** 2026-07-04
- **Series status:** Part 2 is the FINAL published part. The article itself says the next part is "as-yet unpublished" (it would have covered individual game results and shift END locations); `hockeyviz.com/txt/shifts3` returns **404 (checked 2026-07-04)**, so the series ends here. Part 1 is distilled at [`hockeyviz-shifts1.md`](hockeyviz-shifts1.md).
- **Completeness:** the full article was retrieved: intro, three sections ("On-the-fly Shifts", "Shift-start-location Adjustment Coefficients", "Adjusted Shot rates"), an Appendix (full player table), three figure references (`otf-3-shifts.png`, `DNOT-4-shifts.png`, `zsadj-delta-five.png`/`-bandy.png`/`-all.png` — images not fetched), and two in-text tables (coefficients; Joensuu/Shinnimin usage). No substantive body text hides in HTML comments.

## Summary

This is the payoff article of the two-part shifts series: it delivers the "quantitative adjustment for deployment" promised at the end of Part 1. McCurdy first closes the on-the-fly question — OTF shifts sliced by the most-recent-event zone still behave as one family, so "we are justified in treating all on-the-fly shifts as of one piece" (the exact origin of the Magnus undifferentiated OTF category). He then builds a **zone-start adjustment**: in the style of his score-adjustment, each 5v5 shot is weighted by how rare it is given the shift-start context of the skaters on ice — a 4×2 table of shots-for/shots-against weights per shift-start type (OZ 0.80/1.23, NZ 1.28/1.18, DZ 1.33/0.78, OTF 0.95/0.98), with each shot's weight computed as the average of the ten on-ice skaters' coefficients. He explicitly names per-second-of-shift coefficients as a "more subtle" refinement and **declines it "in the interests of simplicity"** — the refinement Magnus later builds as per-second zone terms. Applying the adjustment to all 2014-15 skaters with ≥100 5v5 minutes yields the headline finding: **only 5% of players move more than one percentage point of on-ice shot share, and only two (Joensuu, Gaustad) move more than two** — "At season scales, for almost every regular player, zone starts don't matter." Case studies show the adjustment separating deployment from ability (Malhotra bleeds shots against *even after* accounting for deployment; the "sheltered" Sedin/Karlsson move not at all). Like Part 1 there is **no fatigue, rest, or shot-sequence content** and no shift-feed data-quality discussion.

## Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| hockeyviz-shifts2-D1 | series scope / status | Part 2 delivers the deployment adjustment; a Part 3 covering individual game results and shift END locations is announced as "as-yet unpublished" — and was never published (shifts3 404s, 2026-07-04). | "In the next (as-yet unpublished) article in the series, we'll look at individual game results and shift end locations as well as shift-start locations." | intro |
| hockeyviz-shifts2-D2 | deployment ontology | Where and how a shift starts is the **coach's** decision; everything the player does with it (winning faceoffs, breakouts, offensive-zone holds) is the **player's**. The adjustment prices only the start. On-the-fly starts count as deployment just like faceoff starts (carried from Part 1). | "In very broad strokes, where and how you start your shift is your coaches' decision; what you do with it is yours, including winning or losing faceoffs, breaking the puck out of your end or failing to do so, holding the puck in the offensive zone, or not; etc." | intro |
| hockeyviz-shifts2-D3 | OTF single-category justification | OTF shifts sliced by the zone of the most recent prior event still behave as one family, so all OTF shifts are treated "as of one piece" / "an entity to themselves" — the explicit origin of Magnus's undifferentiated on-the-fly category. | "This suggests we are justified in treating all on-the-fly shifts as of one piece." / "Thus, we proceed by treating ``on-the-fly'' shifts as an entity to themselves." | On-the-fly Shifts |
| hockeyviz-shifts2-D4 | four-type shot-rate comparison | Comparing the four shift-start types: OTF shifts produce shots at very early times and are **persistently higher than faceoff types around 20 s** after shift start; after ~30 s all four types converge to broadly similar rates, clustering around **50–70 shots per sixty minutes**. | "what is somewhat more surprising is that they are persistently higher than the faceoff types in the region around twenty seconds after shift start. Nevertheless, after around thirty seconds, all shift types see broadly similar shot rates, clustering around 50-70 shots per sixty minutes." | On-the-fly Shifts |
| hockeyviz-shifts2-D5 | adjustment method: rarity weighting | Zone-start adjustment built "similar to my method of score-adjustment": each shot is weighted by how rare it was given its shift-start context — shots from OZ starts are cheap (weighted lightly), from DZ starts expensive (weighted highly). | "Using an approach similar to my method of score-adjustment, I weight each shot according to how rare it was, given its context. Shots from offensive-zone starts are easy to come by and thus cheap and weighted lightly; shots from defensive-zone starts are hard to obtain and thus weighted highly." | Shift-start-location Adjustment Coefficients |
| hockeyviz-shifts2-D6 | the coefficient table | Per shift-start type, shots-for / shots-against weights: **OZ 0.80 / 1.23; NZ 1.28 / 1.18; DZ 1.33 / 0.78; On-the-fly 0.95 / 0.98**. OTF is near-neutral by construction; OZ/DZ are near-mirror. | table given verbatim in text | Shift-start-location Adjustment Coefficients |
| hockeyviz-shifts2-D7 | per-shot composition: ten-skater average | Because the ten on-ice skaters at a 5v5 event started their shifts in different places at different times, each shot's weight = the **average of the ten skaters' shift-start-type coefficients**. | "For each event at 5v5, there are ten skaters, not all of which started their shifts in the same place or at the same time. To get a value for each shot, we average the ten corresponding coefficients." | Shift-start-location Adjustment Coefficients |
| hockeyviz-shifts2-D8 | per-second refinement DECLINED | Per-second-of-shift-type adjustment coefficients are named as the "more subtle" method, flagged as "possibly … worth pursuing", and declined "in the interests of simplicity". This is the direct 2015 ancestor of the Magnus per-second zone terms (magnus7 4×60; magnus9 capped at 35 s). | "A more subtle adjustment method would compute adjustment coefficients for each second of each shift type, it is possible that this is an avenue worth pursuing. In the interests of simplicity, I do not do so here." | Shift-start-location Adjustment Coefficients |
| hockeyviz-shifts2-D9 | eligibility threshold | Season-level analysis restricted to skaters with **at least 100 minutes of 5v5 ice time** in 2014-15. | "among all those who played at least 100 minutes at 5v5" | Adjusted Shot rates |
| hockeyviz-shifts2-D10 | headline finding: zone starts don't matter | Only **5% of ≥100-minute players** move more than one percentage point of on-ice shot percentage under the adjustment; only **two players** (Joensuu, Gaustad) move more than two. | "**At season scales, for almost every regular player, zone starts don't matter.**" (bold in original) | Adjusted Shot rates |
| hockeyviz-shifts2-D11 | extreme-case anatomy | The biggest movers are extreme-deployment fourth-liners: Joensuu (33% DZ faceoff starts vs 11% league average; 45.5% raw → ~48.5% adjusted, ≈+3 pp) and Shinnimin (17% OZ vs 12% average; 49.0% → 47.1%, ≈−2 pp). League-average shift-start mix: OZ 12%, NZ 18%, DZ 11%, OTF 59%. | usage table given verbatim | Adjusted Shot rates |
| hockeyviz-shifts2-D12 | sheltered/buried debunk | Reputationally "sheltered" players (H. Sedin, Karlsson) show **no movement** in shot percentage; "buried" Kruger moves just over 1 pp; Malhotra shows a marked shots-against effect but "even after accounting for his deployment he bleeds shots against heavily" — the adjustment separates deployment from ability. | "both Henrik Sedin and Erik Karlsson show no movement whatever in shot percentage … Their shot results are neither inflated nor deflated by their deployment." | Adjusted Shot rates |
| hockeyviz-shifts2-D13 | faceoff-only deployment measures exaggerate | Zone-start measures built on faceoffs only "hugely exaggerate" which players are deployed in heavily offensive/defensive roles (because 59% of shift starts are OTF and near-neutral). The 2015 antecedent of Magnus 9's D44 caveat against OZ/DZ-faceoff-only deployment analyses. | "measures based on (some) faceoffs hugely exaggerate which players are actually being deployed by their coaches in 'heavily' defensive of offensive roles." | Adjusted Shot rates |
| hockeyviz-shifts2-D14 | future work: OTF next-event prediction | Flagged future work: predicting with decent accuracy the location of the next event after an on-the-fly change. (Not realized in any fetched source; inferred unbuilt.) | "This also suggests a future work; namely, developing a way to predict with some decent accuracy the location of the next event following an on-the-fly shift." | On-the-fly Shifts |
| hockeyviz-shifts2-D15 | full-table transparency | Appendix publishes raw and zone-start-adjusted on-ice shot percentage for **every** 2014-15 skater with ≥100 5v5 minutes (with icetime hours and delta) — full-population disclosure, not just the movers. | Appendix table | Appendix |

## Model / method structure sketch

A descriptive adjustment pipeline (no regression, no fitted model):

1. **Shift-start typing** (from Part 1): each skater-shift is typed OZ / NZ / DZ faceoff or on-the-fly.
2. **Coefficient estimation:** per shift-start type, a shots-for weight and a shots-against weight expressing shot rarity given the start context (score-adjustment-style inverse-frequency weighting; the estimation procedure beyond "similar to my method of score-adjustment" is not detailed — see Open questions). 2014-15 data, 5v5.
3. **Per-shot weight:** average of the ten on-ice skaters' applicable coefficients (each skater contributes his own current shift-start-type coefficient; for/against side per the shot's direction relative to each skater's team).
4. **Player aggregation:** re-compute each player's on-ice shot percentage with weighted shots; compare raw vs adjusted at the season level (≥100 min 5v5).

Explicitly declined: per-second-of-shift-type coefficients (D8). Not present: xG weighting (this is 2015, shot-count based), score/venue interaction with the zone-start weights, uncertainty quantification.

**What is NOT in the article:** fatigue, rest, cumulative TOI, or back-to-back content of any kind; any within-sequence shot indexing; stint construction (the Magnus design-matrix concept); shift-feed data-quality discussion; per-second decay estimation (declined).

## Evaluation protocol and reported results

No formal evaluation protocol (no held-out test, no repeatability check on the adjusted measure). Reported results are the season-level application:

- Coefficients: OZ 0.80/1.23, NZ 1.28/1.18, DZ 1.33/0.78, OTF 0.95/0.98 (SF/SA).
- League-average shift-start mix: OZ 12% / NZ 18% / DZ 11% / OTF 59%.
- Largest positive mover: Jesse Joensuu (EDM, ~200 min), 45.5% → ≈48.5% (+~3 pp); largest negative: Brendan Shinnimin (ARI, 128 min), 49.0% → 47.1% (−~2 pp).
- Distribution: 5% of ≥100-min players move >1 pp; 2 players move >2 pp.
- Case studies: Kruger ≈+1 pp; Malhotra marked SA effect, still bleeds SA after adjustment; H. Sedin and Karlsson ≈0 movement.
- Four-type convergence: all shift types ≈50–70 shots/60 after ~30 s.

## Outputs / artifacts

- Figures: OTF shifts by most-recent-event zone (`otf-3-shifts.png`); four shift types together (`DNOT-4-shifts.png`); top-five adjustment deltas (`zsadj-delta-five.png`); named sheltered/buried case studies (`zsadj-delta-bandy.png`); all-players delta plot with >1 pp in blue, >2 pp in red (`zsadj-delta-all.png`).
- In-text tables: the 4×2 coefficient table; the Joensuu/Shinnimin/average usage table.
- Appendix: full raw-vs-adjusted shot-percentage table for all 2014-15 skaters ≥100 min 5v5.

## Linked / companion articles referenced

- https://hockeyviz.com/txt/shifts1 — Part 1 (distilled: [`hockeyviz-shifts1.md`](hockeyviz-shifts1.md)).
- His "method of score-adjustment" is invoked but not linked; the score-adjustment article is not identified from this page.

## Open questions / ambiguities in the source

1. **Coefficient estimation procedure unstated.** "Similar to my method of score-adjustment" is the only description; whether the weights are inverse relative frequencies of shots per start type, how OTF near-neutrality was normalized, and what baseline normalizes the table are all unstated. (inferred: league-average shot rates per start type vs overall average, per Part 1's rate curves.)
2. **Shot universe unstated in this part.** Part 1 measured Corsi (blocks, misses, saves, goals); Part 2 says "shots" and "on-ice shot percentage" without redefining. (inferred: same Corsi universe as Part 1.)
3. **Coefficient time-scope mismatch with Part 1's decay finding.** Part 1 showed the OZ-start effect decays within ~15–20 s, yet the flat coefficients apply to a skater's whole shift (however long); McCurdy acknowledges exactly this with the declined per-second refinement (D8) but does not quantify the misattribution the flat version causes.
4. **OTF share inconsistency (minor).** Part 1: 57% of shifts / 58% of ice time; Part 2 intro recap: "around half"; Part 2 usage table average: 59%. Different denominators (shifts vs player-shift starts) presumably explain it; not reconciled in text.
5. **"Score-adjustment" lineage.** The referenced score-adjustment method is not linked or dated; its weights and estimation would clarify D5/D6.
6. **No repeatability check.** Whether adjusted shot percentage is more predictive/repeatable than raw is not tested — the claim "zone starts don't matter" rests on the small delta magnitudes alone.
7. **Player-name typo.** "Brendan Shinniman" (text) vs "Shinnimin" (table); the player is Brendan Shinnimin. Cosmetic.

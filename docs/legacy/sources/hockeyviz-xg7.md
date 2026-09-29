# HockeyViz — "Magnus 7: xG, Shooting, and Goalie-ing"

- **Title (as published):** "Magnus 7: xG, Shooting, and Goalie-ing" (page `<title>`: "xG 7")
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Published:** June 16, 2023
- **URL used:** https://hockeyviz.com/txt/xg7 — fetched directly via curl with a browser user-agent (WebFetch returns HTTP 403 from hockeyviz.com). Accessed 2026-07-04.
- **Retrieval status:** Full article text retrieved, including all three technical appendixes (Setter Imputation, Blocked Shot Location Imputation, Centering Penalties). Figures/plots referenced in the article are PNGs and were not retrieved; all text below derives from the prose.
- **Scope note:** This is a lineage article. xG8 (May 2025, `sources/hockeyviz-xg8.md`) is the current shipped version. xg7 is distilled here to establish lineage, document the original blocked-origin imputation formula, and support the R3.7 imputer rework. Where xg8 supersedes xg7, that is noted explicitly. Inferences are marked "(inferred)".

---

## Summary

Magnus 7 is the predecessor to xg8 — a three-layer sequential penalized logistic model (at-net / on-net / scored, with xG = p_at · p_on · p_in) fit on two-year pooled windows rather than the single-season chain xg8 introduced. The article covers the same covariate families as xg8 (strength state, hexagonal shot-type fabrics, 5-second previous-event context, rebound delay/shooter identity, game time, score state, shooter/setter/goalie/coach person terms) but with an important structural difference: there is no freeze layer. The "scored vs saved" layer is the terminal outcome. xg8 added the freeze layer in 2025 specifically to model goaltender behaviour more precisely.

The article is most important for the repository as the source of the original **blocked-shot origin imputation** design, reproduced verbatim in a dedicated appendix (`#blockedShotLocationImputation`). McCurdy imputes the true shot origin for blocked shots — the location where the puck left the shooter's stick — from the league-recorded block location using a deterministic closed-form geometric kernel. No learning from data, no conditioning beyond geometry, no explicit uncertainty propagation. The imputed distribution enters the model as fractional design-matrix rows (the same device used for setter imputation). xg8 retains this architecture but tightens the proximity bandwidth by 5× (d²/100 → d²/20).

---

## Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| hockeyviz-xg7-D1 | Layer decomposition (3 layers) | Three sequential conditional logistic submodels: (1) at-net vs blocked, (2) on-net vs missed given unblocked, (3) scored vs saved given on-net. xG = p_at · p_on · p_in. | "In order to answer all of these questions, I have made three interlinked models" + "the xG, the probability that the shot will become a goal, is p = p_at · p_on · p_in" | Estimating Shot Outcomes |
| hockeyviz-xg7-D2 | No freeze layer | Save outcomes are not subdivided into freeze vs in-play in xg7. The terminal layer is scored vs saved only. Freeze handling was explicitly deferred. | "one thing that I have deferred until 2024 is the question of detailed save outcomes" | Things That I Intend To Do Next Year / Detailed Save Outcomes |
| hockeyviz-xg7-D3 | Fit window: two-year pairs | Model is fit on pairs of seasons. Displayed results are from 2021-22 + 2022-23. Prior estimates come from 2019-20 + 2020-21, chained back to 2007-08. | "one big improvement in Magnus 7, however, is that the fundamental unit of time is _pairs_ of seasons, because it improves out-of-sample predictions, especially in the estimates of shooter and goaltender talent" | Results |
| hockeyviz-xg7-D4 | Base rates | ~15% of shots blocked (85% at-net, ~+1.86 logits); ~75% of unblocked shots on-net (~+1 logit); ~5% goal rate given on-net (~−2.2 logits). | explicit constant-term annotation on the logistic-function figure | Probability In Regression |
| hockeyviz-xg7-D5 | Shot type: geographic fabrics | In-zone shots split by shot type with independent hex fabrics per type. Sub-types: wrist/snap, slapshot (EV+EA vs special teams treated separately via seam-target term), tip/deflection (restricted fabric), backhand (small fabric + perimeter), wraparound. Out-of-zone and below-goal-line shots get their own region terms. | "the geometric character of the patterns of in-zone shots, though, depends strongly on the type of shot employed" (credits Michael Schuckers) | Regions of the Ice and Shot Type |
| hockeyviz-xg7-D6 | Hex resolution | Hexagons with ~88 cm sides (~2 m² / 22 sq ft each). Coarser than prior versions. Symmetrized L/R. | "This is partially for computational efficiency, partly for simplicity, and partly for what we might call 'data honesty'" — league shot locations reliable only to ~88 cm | Specific Shot Locations |
| hockeyviz-xg7-D7 | L/R symmetrization | Hex fabrics artificially symmetrized across the split line; shots from both sides pooled. | "if there are non-trivial left-right disparities at the league level I will not discern them" | Specific Shot Locations |
| hockeyviz-xg7-D8 | Slapshot seam-target term | Slapshots get an additional seam-target scalar: exp(−dist_from_seam² / 100), capturing one-timer clustering at "seam" spots ~15 ft from split line and ~14 ft from goal line. Separate terms for EV+EA vs special teams. | "a large fraction of slapshots are one-timers, and, especially on special teams, these one-timers tend to cluster" | Slapshots |
| hockeyviz-xg7-D9 | Tip location imputation | Tips recorded outside the restricted tip fabric get their location moved 4/5 of the way toward the far post (or, if on the split line, toward the middle of the goal line). Same approach as xg8. | "I impute a plausible actual tip location by moving the location four-fifths of the way from its existing location towards the far post" | Tips and Deflections |
| hockeyviz-xg7-D10 | Backhand perimeter | Backhands outside the small backhand fabric assigned to "perimeter". | "I do not consider them to be serious attempts to score" | Backhands |
| hockeyviz-xg7-D11 | Blocked-shot origin imputation: concept | The league records block location, not shot origin. McCurdy imputes the true shot origin — where the puck left the shooter's stick — using a deterministic geometric kernel applied to the hex grid. The imputed distribution enters the design matrix as fractional rows (same device as setter imputation). | "the league does not record, for blocked shots, the location of the original shot, but instead the location of the block itself. For my purposes, I require the original shot location, and so for model training I've employed an imputation process where I make an educated guess of where a shot could have come from given where it was blocked." | Blocked Shot Trickery; Appendix: Blocked Shot Location Imputation |
| hockeyviz-xg7-D12 | Blocked-shot origin imputation: formula | For a block at (x,y), each hex with centre (a,b) closer to centre-ice than y is scored: `exp(−s²/30) · exp(−d²/100)`, where s = distance from goal centre to where the (a,b)→(x,y) line crosses the goal line (off-centre measure), and d = distance between (a,b) and (x,y). P(hex) = score / sum_scores. Two factors: "weakly proportional to how close it is to the block location, since most shot blocks are caused by proximity pressure, and strongly proportional to how 'on line' a shot from such location would be." | verbatim formula from the appendix: `\exp(-s^2/30)\exp(-d^2/100)` | Appendix: Blocked Shot Location Imputation |
| hockeyviz-xg7-D13 | Blocked-shot origin: no conditioning | The imputation kernel conditions only on geometry (block point location and hex grid). No conditioning on strength state, score, prior event, shot type, era, or venue. No learning from data. No validation of the imputer reported anywhere in the article. | (inferred from absence) | Appendix: Blocked Shot Location Imputation |
| hockeyviz-xg7-D14 | Blocked-shot origin: uncertainty handling | No explicit uncertainty propagation. Fractional design-matrix rows effectively integrate the imputed distribution at training time; at inference the same kernel generates a pseudo-distribution. There is no separate uncertainty estimate for the imputed origin, no interval, and no scoring-rule check. | (inferred from the fractional-row device: it averages the kernel rather than propagating posterior uncertainty) | Appendix: Blocked Shot Location Imputation |
| hockeyviz-xg7-D15 | Previous-event context: 9 categories | Fixed 5-second window; 9 centred terms: 5s of nothing (open play), shot from this zone, shot from other zone, turnover this zone, turnover other zone, hit this zone, hit other zone, faceoff this zone, faceoff other zone. Gives/takes pooled into one "turnover" category. | "I've arbitrarily fixed a window of five seconds as 'recent context'" | Previous Events |
| hockeyviz-xg7-D16 | Previous-event structure vs xg8 | xg7 uses a flat 9-category table. xg8 restructured into open-play / cycle (6 sub-terms) / rush (5 sub-terms) with more resolution on both cycle and rush shot types. The xg7 category "shot from other zone" is the predecessor of xg8's rush concept; "shot from this zone" is the predecessor of xg8's cycle rebound sub-terms. | (comparison inferred from both articles) | Previous Events |
| hockeyviz-xg7-D17 | Rebound delay buckets | Rebounds (shot-after-shot) get 6 centred terms for delay in seconds: 0, 1, 2, 3, 4, 5. Bang-bang (delay 0) highest scoring; delay 1 unexpectedly bad. | "it makes a surprising difference to shot success precisely how far apart the two shots are" | Rebound Delays and Rebound Shooters |
| hockeyviz-xg7-D18 | Rebound shooter identity | Centred pair: rebound by same shooter vs by a teammate. Teammate rebounds more successful. | "rebounds that are taken by _other_ shooters are considerably more successful" (suggested by Cody Magnusson) | Rebound Delays and Rebound Shooters |
| hockeyviz-xg7-D19 | Game time terms | Centred triple: first / middle / final minute of regulation period. Per-minute breakdown rejected for lack of OOS gain. | "Dividing the 'middle' term into eighteen per-minute terms does not improve prediction accuracy" | Game State Proxies |
| hockeyviz-xg7-D20 | Score state terms | Centred 9-way: leading/tied/trailing × period 1/2/3. No garbage-time term (tested and rejected, unlike xg8 which added it). | "Instead of the simple leading/tied/trailing terms that I settled on, I explored using specific score states (1-0, 2-0, and so forth). This improved nothing. I also considered a 'garbage time' term ... but found nothing of value here." | Game State Proxies; Things That Did Not Help: Detailed Score States |
| hockeyviz-xg7-D21 | Shooter person terms | Triple of centred shooter terms (one per submodel: block, miss, score). Shooter identity NOT used for tip/deflection shots in xg7 (same decision as xg8). | "this year I have discovered that the best predictions are obtained by assuming that the person tipping the puck does not, in general, do so according to any particular skill" | Shooters |
| hockeyviz-xg7-D22 | Setter imputation | Same design as xg8: goals use recorded primary assister; non-goals impute a probability distribution over on-ice teammates. Proportions from Sznajder data: forward shot → other forwards 2× vs defenders; defender shot → forwards 3× vs the other defender; all × 80% (20% unassisted). Fractional design matrix rows. Setter terms in all three layers in xg7 (unlike xg8 which drops setters from the block and miss layers). | "Adding setting terms to the submodels for blocks and misses increases their predictive power on out-of-sample shots by such a small amount that I felt it better not to include them at all" — this sentence describes the xg8 decision; in xg7 the article text implies setter terms ARE in all submodels, citing Sznajder data | Setters; Appendix: Setter Imputation |
| hockeyviz-xg7-D23 | Setter terms: all three layers | In xg7, setter terms appear in all three submodels (block, miss, scored). xg8 dropped them from the block and miss layers for insufficient OOS gain. (inferred from the article structure: xg8's decision to drop them is described as a new decision, implying they were included before.) | (inferred from xg8's explicit "this year I decided not to include them in block/miss layers" framing — see hockeyviz-xg8-D34) | (inferred) |
| hockeyviz-xg7-D24 | Goalie terms | No goalie term in the block layer. Goalie terms in on-net (miss-forcing) and scored layers. Miss-forcing judged a "real" skill. | "it would be silly to include terms in the block-vs-at-net submodel, since goaltenders don't exert any influence in practice on whether or not the skaters on their team block shots" | Goaltending |
| hockeyviz-xg7-D25 | Coach terms | Two centred terms per head coach per submodel: impact on own team's shots and on opponents' shots. Same architecture as xg8. | "I've introduced new terms in each submodel for each head coach" | Coaches |
| hockeyviz-xg7-D26 | Static penalties: person terms | Global penalty of 100 multiplied by per-type multipliers. Effective penalties: shooters 50, setters 50, goalies 300, coaches for/against 1000 each. Structural terms (strength, region, rebound, score, time, hex): effective 1. Constant: 0 (unpenalized). | penalty table with global multiplier of 100 | Static Penalties |
| hockeyviz-xg7-D27 | Penalty encoding vs xg8 | xg7 reports effective penalties after a global 100 × per-type multiplier: shooters 50, setters 50, goalies 300, coaches 1000. xg8 reports different values directly: shooters 0.2, setters 0.2, goalies 30, coaches 1000. The numeric constants are source facts, but their magnitudes alone do **not** identify a wider or narrower fitted distribution across models with changed populations, designs, objectives, and scaling. | constants transcribed from the two articles; cross-version distribution claim deliberately withheld | Static Penalties; cf. hockeyviz-xg8-D43 |
| hockeyviz-xg7-D28 | Fabric fusion penalties | Adjacent hex pairs p,q fused with strength c_pq proportional to the overlap area of the shooter-to-goalpost triangles from each hex. Same geometric construction as xg8. | "nearby shots should have similar results for that reason, purely on physical grounds" | Fabric Penalties |
| hockeyviz-xg7-D29 | Dynamic penalties: two-year window | Fit seasons 2007-08 to present as two-year pairs. Prior from the previous two-year window. Rookies receive a prior of 0 (average) with diagonal penalty of 0.001. | "fitting this model over each season from 2007-2008 until the present" + "for players for whom there is no prior (rookies) I use a prior of 0 with a very mild diagonal penalty of 0.001" | Dynamic Penalties |
| hockeyviz-xg7-D30 | Centering penalties | Constraint enforced by adding a multiple of c_s · c_t to the off-diagonal entries of K. Multiple used: 10^18 in xg7 (vs 10^6 in xg8). | "I used 10^18 for this purpose" | Appendix: Centering Penalties |
| hockeyviz-xg7-D31 | Rejected: shift fatigue | Average time-in-shift of shooting and defending teams tested in multiple permutations. No improvement to prediction accuracy. | "in no instance did these terms improve prediction accuracy to speak of" | Things That Did Not Help: Shift Fatigue |
| hockeyviz-xg7-D32 | Rejected: time between shots | Time since last shot faced by the goaltender tested. No effect found. | "I could not find any such effect" | Things That Did Not Help: Time Between Shots |
| hockeyviz-xg7-D33 | Rejected: diffuse individual impact | General per-player on-ice impact terms (offensive + defensive) for every on-ice player. Predictions worsened. Same conclusion as xg8. | "Including such general terms makes predictions of future results weaker; in particular I found no evidence that defending players have a general impact on per-shot success" | Things That Did Not Help: Diffuse Individual Impact |
| hockeyviz-xg7-D34 | Rejected: detailed score states (xg7) | Specific score differentials (1-0, 2-0, etc.) and garbage-time terms tested. Neither improved predictions. xg8 subsequently added garbage-time after further investigation. | "Instead of the simple leading/tied/trailing terms that I settled on, I explored using specific score states ... I also considered a 'garbage time' term ... but found nothing of value here." | Things That Did Not Help: Detailed Score States |
| hockeyviz-xg7-D35 | Deferred to xg8: freeze layer | Detailed save outcomes (freeze vs deflection vs battle) deferred to the following year. Became xg8's new Layer 3 (in-play vs frozen) + Layer 4 split. | "Every year contains more ideas than I have the time or computers to properly explore; one thing that I have deferred until 2024 is the question of detailed save outcomes" | Things That I Intend To Do Next Year: Detailed Save Outcomes |
| hockeyviz-xg7-D36 | Deferred: stoppages model | Separate model measuring skater impact on stoppages in all three zones; planned as a link to the xG model. Status in xg8 is not described. | "I have a model in preparation with which I mean to estimate skater impact on stoppages in all three zones" | Things That I Intend To Do Next Year: Stoppages |

---

## Model structure sketch

Three-layer sequential conditional cascade (xg7):

```
shot taken (any attempt; empty-net / penalty / shootout excluded)
  └─ Layer 1: at net vs BLOCKED          p_at   (blocked-origin imputed via geometric kernel)
      └─ Layer 2: on net vs MISSED        p_on
          └─ Layer 3: GOAL vs SAVED       p_in
xG = p_at · p_on · p_in
```

**Key difference from xg8:** There are three layers, not four. The "scored vs saved" layer in xg7 conflates what xg8 splits into frozen/in-play and goal/rebound. xg8's Layer 3 (freeze) and Layer 4 (goal) together replace xg7's single Layer 3.

Each layer is a penalized logistic regression (GLM, logit link). Per-layer differences:
- **Goalies:** absent from Layer 1; present in Layers 2 and 3.
- **Setters:** present in all three layers in xg7 (xg8 drops them from Layers 1-2 for insufficient OOS gain).
- **Shooters:** present per-layer, except tips/deflections.
- **Blocked shots:** enter Layer 1 via imputed origin distribution (fractional design-matrix rows); the same imputed origin is used in Layers 2 and 3 for those shots.
- **Coaches:** two terms per head coach per layer.
- **Fit window:** two-year rolling pairs, not single-season.

---

## Blocked-shot origin imputation (full detail)

### What is imputed

The league records where a shot is blocked (the blocker's position), not where the shot was taken. McCurdy imputes the **true shot origin** — the rink position where the puck left the shooter's stick.

### The algorithm (verbatim from the article appendix)

> "if a shot is blocked at location (x,y), I consider all of the hexes whose centre (a,b) has second coordinate closer to centre-ice than y. For each such hex I compute a score exp(−s²/30) · exp(−d²/100), where s is the distance between the centre of the goal and the intersection of the goal line with the line joining (a,b) to (x,y) and d is the distance between (a,b) and (x,y). I assign each hexagon as possibly being the original shot location with probability equal to its score divided by the sum of all of the scores."

**Candidate set:** All hexes whose centre-y is closer to centre-ice than the block point y. (Hexes between the block and the net — i.e., net-side of the block — are excluded as impossible shot origins.)

**Scoring kernel:** Two multiplicative factors:
- `exp(−s²/30)` — s measures off-line-ness: how far from goal centre the implied shot trajectory (hex→block point extended to the goal line) misses. Denominator 30 is shared with xg8. Small s (shot "on line" toward the net) is favoured.
- `exp(−d²/100)` — d measures proximity: hex-to-block-point distance. Denominator 100 in xg7 (changed to 20 in xg8 — see lineage note below). Small d (hex close to block) is weakly favoured.

**Normalization:** P(hex) = score(hex) / Σ scores over all candidate hexes.

**Author's characterization:** "The chance for a given hex is thus both weakly proportional to how close it is to the block location, since most shot blocks are caused by proximity pressure, and strongly proportional to how 'on line' a shot from such location would be."

(The word "weakly" for proximity and "strongly" for on-line-ness is consistent with the larger denominator on the d term relative to the s term in xg7. xg8's tightening of d²/100 → d²/20 shifts the balance toward stronger proximity influence.)

### Data source

Pure closed-form geometry. No training on observed data, no regression against unblocked-shot origin pairs, no tracking-era measurements. The formula's constants (30, 100) are hand-chosen, not learned.

### Uncertainty handling

None. The imputed probability distribution enters the design matrix as fractional rows during fitting — the same technique as setter imputation. This gives each candidate hex a contribution proportional to its probability, implicitly averaging the location effect over the imputed distribution. There is no separate imputation-uncertainty interval, no explicit propagation to the final xG value, and no reporting of imputer uncertainty to the user.

### Validation

None reported. The article contains no scoring-rule evaluation, no calibration check, no comparison to a baseline, and no held-out test of the imputer's accuracy.

### Entry into the layered model

The imputed distribution feeds ALL three layers via the hexagonal fabric columns. For training: blocked shots generate fractional design-matrix rows, one per candidate hex, weighted by P(hex). For inference: same kernel generates the imputed distribution and the same fractional-row construction applies.

---

## Lineage note: xg7 → xg8 changes

| aspect | xg7 | xg8 |
|---|---|---|
| Layer count | 3 (blocked / missed / scored) | 4 (blocked / missed / frozen / scored) |
| Fit window | Two-year pairs | Single-season with chaining since 2007-08 |
| Blocked-origin d-term | exp(−d²/100) | exp(−d²/20) — 5× narrower, proximity matters more |
| Blocked-origin s-term | exp(−s²/30) | exp(−s²/30) — **unchanged** |
| Score: garbage-time | rejected | new term in xg8 |
| Setter layers | all three layers | Layers 3-4 only (dropped from 1-2) |
| Centering penalty constant | 10^18 | 10^6 |
| Person penalty magnitudes | global 100 × {shooters 0.5, goalies 3, coaches 10} = {50, 300, 1000} | absolute {0.2, 30, 1000} — goalies 10× narrower |
| Previous-event structure | flat 9 categories | open-play / cycle-6 / rush-5 sub-terms |
| Rush/cycle resolution | "shot from other zone" / "shot from this zone" | explicit rush + cycle sub-term families |
| Sequence fatigue term | absent | NEW in xg8 (shot index 1/2/3/4+ while defending skater on ice) |

---

## Feature / covariate list (as stated in xg7)

Per layer (logit-additive):
1. **Constant** (per-layer base rate)
2. **Strength state:** PP, PPv3, SH, EA, EV (4v4+5v5), 3v3. Centred.
3. **Region:** out-of-zone; below goal line; in-zone (the remainder). Centred.
4. **Shot type (in-zone):** wrist/snap, slap (EV+EA), slap (special teams), tip/deflection, backhand, wraparound. Centred.
5. **Location:** hex fabric per shot type (88 cm sides, L/R symmetric); tip fabric restricted; backhand fabric + perimeter; blocked shots via imputed origin distribution; out-of-fabric tips moved toward far post. 15 centred fabrics (inferred; article says "fifteen fabrics").
6. **Slapshot seam-target scalar:** exp(−dist²/100) for each slapshot; separate EV+EA and special-teams terms.
7. **Previous-event context (5 s window):** 5s of nothing; shot this zone; shot other zone; turnover this zone; turnover other zone; hit this zone; hit other zone; faceoff this zone; faceoff other zone. Centred.
8. **Rebound delay:** 0, 1, 2, 3, 4, 5 seconds. Centred.
9. **Rebound shooter:** same shooter vs teammate. Centred.
10. **Time-in-period:** first / middle / final minute of regulation period. Centred.
11. **Score state:** leading/tied/trailing × period 1/2/3. Centred. (No garbage-time term.)
12. **Shooter identity** (except tips). Centred league-wide.
13. **Setter identity** (all three layers; imputed fractional encoding; ×80% unassisted discount). Centred.
14. **Goalie identity** (Layers 2-3). Centred.
15. **Coach for / coach against** (per head coach, per layer). Each centred.

**Not included:** team identities; shooter terms on tips; location-specific person terms; general on-ice impact terms; detailed score differentials; shift fatigue; time between shots; sequence/fatigue index (added in xg8); open-play/cycle/rush sub-structure (added in xg8); freeze layer (added in xg8).

---

## Evaluation protocol and reported results

**Protocol:** Out-of-sample predictive comparison as the gate for including vs excluding terms, paired with intrinsic plausibility. Same philosophy as xg8. No overall headline accuracy metric (AUC, log-loss, calibration) is reported for xg7 in the article.

**Quantitative results reported:**
- Base rates: ~15% blocked; ~75% on-net given unblocked; ~5% scored given on-net.
- Strength state logit impacts: PPv3 shots scored +0.64 logits above average; EA blocked −0.23 logits (harder to block than average).
- Location terms span ~±2.5 logits per shot type per layer (same as xg8 characterization).
- Rebound delay 0 s (bang-bang): scored +0.84 logits; delay 1 s: blocks −0.23, scored −0.17 (unexpectedly poor).
- Out-of-zone shots: at-net +3.70 logits (almost never blocked), scored −3.56 logits (almost never scored).
- Results table for the 2021-23 fitted model; prior estimates from 2019-21 window.

---

## Outputs / artifacts

- Per-shot xG (product of three layer probabilities) for all shots including blocked attempts with imputed origins.
- Per-layer person estimates (shooter triple, setter triple, goalie pair, coach pairs) as league scatter plots per layer.
- Historical term plots for all structural terms (2007-08→2022-23).
- Per-player sub-skill breakdown pages (subscribers).

---

## Open questions / ambiguities in the source

1. **"Fifteen fabrics"**: The article states "each one of these fifteen fabrics is centred" but the text describes eight shot-type/region categories (out-of-zone, below goal line, wraparound, wrist/snap, backhand, tip/deflection, slapshot special-teams, slapshot EV+EA). The 15 is likely 5 in-zone shot types × 3 layers = 15, or a different per-type count. The exact tally of distinct fabrics is ambiguous without the figures (which are PNGs, not retrieved).

2. **Slapshot denominator in seam-target formula**: The article gives exp(−dist²/100) for the seam-target scalar but does not state whether this 100 is in feet² or metres², which affects the effective bandwidth. The hex-grid distance denominator in the imputation formula (d²/100) uses the same numerical value; whether these share a units convention is not stated.

3. **Setter terms in all layers**: The article does not explicitly state that setter terms appear in all three submodels — it says adding them to blocks/misses increases OOS power by "such a small amount" that xg8 dropped them. For xg7 this implies they WERE included (the xg8 decision was a new one), but the article does not confirm this directly (inferred).

4. **Dynamic penalty for non-person terms**: xg7's dynamic-penalty section focuses on person terms. Whether hex location terms are also chained season-to-season (as in xg8-D49) is not stated.

5. **Imputation at inference vs training**: The article says the imputer is used "for model training." Whether the same fractional-row device is also used at inference time (scoring a new season's blocked shots) or whether a point estimate is substituted is not stated. xg8 also leaves this implicit; (inferred) the same distribution applies at scoring time.

6. **Centering penalty constant 10^18 vs 10^6**: The article states 10^18. xg8 uses 10^6 and notes that very large values "can cause oscillations." Whether the 10^18 caused numerical issues in xg7 is not discussed.

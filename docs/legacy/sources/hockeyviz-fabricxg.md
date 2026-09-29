# HockeyViz — "Magnus 3: xG, Shooting, and Goalie-ing"

- **Title (as published):** "Magnus 3: xG, Shooting, and Goalie-ing"
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Published:** March 26, 2020
- **URL used:** https://hockeyviz.com/txt/fabricxg — full article retrieved from pre-fetched HTML
  (curl with browser user-agent `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like
  Gecko) Chrome/120.0 Safari/537.36`; WebFetch returns HTTP 403 from hockeyviz.com).
- **Accessed:** 2026-07-04
- **Completeness:** Full article retrieved. Sections verified against heading inventory: h3 tags
  "Estimating Shot Difficulty", "Vital Theoretical Preliminaries", "Odds vs Probability", "Method",
  "The Geometric Terms", "Fitting", "Static penalties", "Dynamic Penalties", "Computational
  delicacies", "Results", "Geometry Results", "Strength, Score, Rush, and Rebound Terms", "Player
  Results". Hex-fabric images and interactive result tables are referenced but not retrieved (PNGs
  and JavaScript-rendered tables); all prose is recovered in full. Historical per-season result links
  (2007-08 through 2018-19) are navigation only.

---

## Summary

This is the write-up for Magnus 3, McCurdy's third-generation expected-goals model (2020 vintage,
fit on data 2007-08 through 2019-20). The model is a **single-outcome penalized logistic regression**
estimating P(goal | unblocked shot), with one unified logit per shot. The conceptual animating idea
is a three-fold skill decomposition: (1) all skaters collectively produce the shot pattern and
determine xG; (2) the shooter can, on top of that, affect goal probability by executing the shot
skillfully; (3) the goaltender can affect probability after the shot is taken. This decomposition
is what makes per-shooter finishing impact and per-goalie save quality identifiable as additive logit
terms after xG is conditioned out.

Covariates include: shooter and goaltender indicators; per-shot-type hexagonal location fabrics
(five shot types; hex subset covering 95% of that type's historical shots); a single indicator for
below-goal-line shots; a neutral-zone (out-of-zone) indicator; rush and rebound indicators; score
state (leading / trailing); and four strength-state terms (SH, PPv3, PP, 3v3) with EV = 4v4+5v5 as
baseline. There are no setter terms, no sequence/fatigue terms, no clock terms, and no coach terms.
Fitting uses penalized MLE with static ridge + hex-fusion penalties (matrix K) and dynamic
season-to-season priors (matrix Λ, vector β₀). Iterative reweighted updates (van Wieringen §5.2)
solve the penalized likelihood. Fit sequentially season by season from 2007-08, each year's
estimates becoming the next year's prior; rookie prior = 0 with a mild 0.001 penalty.

Key reported findings (2019-20 season): SH +24% odds, 3v3 +62%, PP +52%, PPv3 +104%, rush +104%,
rebound +101%, trailing −7%, leading ~+1%; below-goal-line base 6.2%, neutral zone 0.4%,
wraparound 4.6%. Best goalie that season (Hellebuyck) ~−12% odds impact; Dubnyk ~+14%.

**Cross-check headline:** xG0 (the deliberately impoverished location+strength-only reference model
used for shot-map ratio weighting) is **NOT** defined in this article. See §Cross-check below.

---

## Decision inventory

| id | topic | decision | rationale / verbatim quote | section |
|---|---|---|---|---|
| hockeyviz-fabricxg-D1 | Skill decomposition (three-fold) | xG = shot-pattern quality produced by all skaters; finishing impact = shooter's per-shot additive logit contribution; goaltending = goalie's per-shot additive logit contribution. Three terms sum in logit space. | "My animating assumption is that all of the skaters … are working together both to generate shots for their team and to suppress the generation of shots by the other team … the shooter themself can, in principle, affect the goal likelihood of the shot … a goaltender can, in principle, affect the goal likelihood of a shot after it is taken" | Vital Theoretical Preliminaries |
| hockeyviz-fabricxg-D2 | Goaltending scope | Goalie impact measured ONLY on shots already taken; this explicitly excludes puck-handling and other pre-shot goalie skills. | "including goaltender effects only on shots already taken prevents us from making any estimate of goaltenders' impact on xG, conceded or generated, from, say, their tendency to handle the puck" | Vital Theoretical Preliminaries |
| hockeyviz-fabricxg-D3 | Shot definition | "Shot" = unblocked shot; goals, saves, and misses (including post/crossbar). Blocked shots excluded throughout. | "when I say 'shot' I will mean 'unblocked shot', that is, goals, saves, and misses (including shots that hit the post or the crossbar)" | Vital Theoretical Preliminaries |
| hockeyviz-fabricxg-D4 | Strength scope | All shots taken at a net with a goalie (any strength state); expanded vs the predecessor model which used only 5v5 and 5v4. | "In contrast to last year's model, which used only 5v5 and 5v4 shots, now I use all shots taken at a net with a goalie, one way or another, as input data." | Vital Theoretical Preliminaries |
| hockeyviz-fabricxg-D5 | Model class | Single-outcome logistic regression: Y ~ l(Xβ), where Y = 1 for goal, 0 for save/miss, l = logistic function. One P(goal) per shot; no layer decomposition. | "The observation vector Y is 1 for goals and 0 for saves or misses. The model itself is … a generalized linear one" | Fitting |
| hockeyviz-fabricxg-D6 | Design matrix — covariates | Columns: (1) shooter indicator; (2) goaltender indicator; (3) geometric terms per shot type (hex fabrics); (4) rush indicator; (5) rebound indicator; (6) leading indicator; (7) trailing indicator; (8) four strength indicators (SH, PPv3, PP, 3v3). | design matrix description in Method section | Method |
| hockeyviz-fabricxg-D7 | Rush definition | Rush = previous recorded PBP event was in a different zone AND no more than four seconds prior. | "shots for which the previous recorded play-by-play event is in a different zone and no more than four seconds prior" | Method |
| hockeyviz-fabricxg-D8 | Rebound definition | Rebound = previous recorded PBP event was another shot by the same team no more than three seconds prior. | "shots for which the previous recorded play-by-play event is another shot taken by the same team no more than three seconds prior" | Method |
| hockeyviz-fabricxg-D9 | Strength categories | SH (fewer skaters), PPv3 (team has >3 skaters vs exactly 3), PP (all other power-play, i.e. team has more skaters but opponent has ≥4), 3v3 (both teams exactly 3, mostly OT); EV = all 4v4 and 5v5 pooled as the reference baseline. | "All shots are assigned exactly one of the above indicators, which should all be understood as the change compared to a similar shot at even-strength, that is, all 4v4 and 5v5 shots gathered together." | Method |
| hockeyviz-fabricxg-D10 | Geometric terms: per-type hex fabrics | In-zone shots modelled with per-shot-type hex fabrics; each fabric covers ≥95% of all historical shots of that type (2007-08 onward). Shot is assigned to the nearest hex in the fabric of its type. Five fabrics: wrist/snap (734 hexes), slap (658), backhand (433), tip/deflection (184); wraparound handled separately. | "consider a hexagonal grid of cells … to each of the five shot types, I define a 'fabric', that is, a subset of these cells which contain at least 95% of all of the shots of that type since 2007-2008" | The Geometric Terms |
| hockeyviz-fabricxg-D11 | Wraparound treatment | Wraparound = single indicator (no hex fabric); locations cluster tightly near the two goalposts; spatial variation in goal likelihood too small to justify fabric. | "I found that shot locations clustered very tightly in the two obvious locations (near the goalposts) and that the spatial variation in goal likelihood was extremely small. Thus, I chose to use a simple indicator for wraparounds, without encoding additional geometric detail" | The Geometric Terms |
| hockeyviz-fabricxg-D12 | Broad-region indicators | Two additional indicator covariates outside the hex fabrics: (1) below-goal-line origin (single indicator); (2) neutral zone origin (from behind the blue line, single indicator). All other shots fall into the in-zone / in-fabric path. | "For shots recorded as originating below the goal line, I use a single indicator variable; similarly a 'neutral zone' indicator for shots originating from behind the blue line." | The Geometric Terms |
| hockeyviz-fabricxg-D13 | Shot-type credit (Schuckers) | Modelling geometry separately per shot type credited to Michael Schuckers. | "I especially appreciate Michael Schuckers, who brought the importance of attacking geometric variation separately by shot type to my attention." | The Geometric Terms |
| hockeyviz-fabricxg-D14 | Static penalty structure | Penalized MLE; static penalty matrix K with three types of entries: (1) diagonal 100 for each goalie and shooter term; (2) diagonal 0.1 for each fabric hex; (3) fusion 5 between each pair of adjacent hexes. Non-person, non-hex structural terms (strength, rush, rebound, score, shot type, below-goal-line, NZ) are unpenalized. | "a diagonal penalty of 100 for each goalie and shooter term, a diagonal penalty of 0.1 for each fabric hex, and a fusion penalty of 5 between each two adjacent hexes. The other terms … are unpenalized" | Static penalties |
| hockeyviz-fabricxg-D15 | Penalty rationale | Diagonal 100 for shooters/goalies encodes prior that NHL players' abilities "cannot therefore be understood to be not-too-far from NHL average (that is, zero)"; hex penalties allow slow variation in geometry by fusing neighbours, "effectively lowers the number of covariates in the model" to help mitigate overfitting. | "The substantial diagonal penalty for shooters and goalies encodes our prior understanding that all of the shooters and goalies are (by definition) NHL players, whose abilities cannot therefore are understood to be not-too-far from NHL average" | Static penalties |
| hockeyviz-fabricxg-D16 | Dynamic penalty structure | Season-to-season prior chain: β₀ = point estimates from previous year; Λ = diagonal of uncertainty estimates from previous year. Penalty term (β − β₀)ᵀΛ(β − β₀). For rookies and 2007-08 (no prior data): prior β₀ = 0 (average), mild diagonal Λ = 0.001. | "I use a prior of 0 (that is, average) with a very mild diagonal penalty of 0.001" | Dynamic Penalties |
| hockeyviz-fabricxg-D17 | Dynamic penalty rationale | Player ability "varies slowly"; accumulating knowledge across seasons preserves signal in sparse data; if only a single season were of interest, dynamic penalties would be irrelevant. | "we imagine that our estimates for players describe athletic ability, which varies slowly" | Dynamic Penalties |
| hockeyviz-fabricxg-D18 | Fitting objective | Maximize penalized log-likelihood: L − βᵀKβ − (β − β₀)ᵀΛ(β − β₀). | equation stated verbatim | Computational delicacies |
| hockeyviz-fabricxg-D19 | Solver | Iterative reweighted update (van Wieringen §5.2 variant); closed-form update β_{n+1} = (XᵀW_nX + Λ + K)⁻¹ Xᵀ(W_nXβ_n + Y − Y_n) + Λ(XᵀW_nX + Λ + K)⁻¹β₀; convergence guaranteed when K and Λ are positive definite ("which they are"). | explicit update formula given | Computational delicacies |
| hockeyviz-fabricxg-D20 | Fit range | Model fit to each regular season 2007-08 through 2019-20 sequentially; estimates from each summer fed as priors into the following year. | "I have fitted this model to each regular season from 2007-2008 through to 2019-2020" | Results |
| hockeyviz-fabricxg-D21 | Strength / context odds ratios (2019-20) | SH +24%, 3v3 +62%, PP +52%, PPv3 +104%, rush +104%, rebound +101%, leading +0.9%, trailing −7.0% (odds ratios relative to even-strength). | table in Strength, Score, Rush, and Rebound Terms | Strength, Score, Rush, and Rebound Terms |
| hockeyviz-fabricxg-D22 | Score effect asymmetry | Trailing teams shoot worse (−7%); leading teams show "negligible change" (~+1%). Author notes this is more interesting than the symmetric story one might expect. | "trailing teams shoot worse than tied teams, but leading teams show negligible change for that reason" | Strength, Score, Rush, and Rebound Terms |
| hockeyviz-fabricxg-D23 | Geometry result — spatial patterns | Wrist/snap: highest in low slot, sharp drop outside the dots; slap: highest in slot but distance-based not dot-based falloff; backhand: high-quality area more concentrated, biased to right-hand side of net (attributed to left-handed shooter overabundance + left-catching goalie overabundance); tip/deflection: low slot + sides of net. | figure captions under Geometry Results | Geometry Results |
| hockeyviz-fabricxg-D24 | Geometry result — base rates (2019-20) | Below-goal-line base probability: 6.2%; neutral zone: 0.4%; wraparound: 4.6%. | bullet list under Geometry Results | Geometry Results |
| hockeyviz-fabricxg-D25 | Goaltender display convention | Goalie values shown on an inverted scale (better performances at top); a good goalie has a NEGATIVE logit impact (lowers shot-odds). Example: Hellebuyck best at ~−12% (lowers 9% shot's odds by 12%), Dubnyk ~+14% (raises odds). | "I've inverted the scale so that the better performances are at the top" | Player Results |

---

## Model structure sketch

Magnus 3 is a **single-stage** penalized logistic regression — one P(goal | shot) — not a multi-layer
cascade. The design matrix Xβ is a sum of terms in logit space:

```
logit P(goal) = constant
              + location fabric term (hex for shot type, or broad-region indicator)
              + shooter term
              + goaltender term
              + rush indicator
              + rebound indicator
              + strength-state indicator (one of SH / PPv3 / PP / 3v3 / implicit EV)
              + score-state indicator (leading / trailing / implicit tied)
```

The logistic function converts the sum to P(goal). All terms are additive in logit space; there is no
interaction term between any of these covariates. All structural terms (strength, rush, rebound,
score, shot type, below-goal-line, neutral-zone) are unpenalized; person terms are penalised by
large diagonals; hexes are penalized by small diagonals + inter-hex fusion.

### What is absent vs xG8 (2025)

| missing in Magnus 3 | present in xG8 |
|---|---|
| No layer decomposition | 4 sequential conditional layers (blocked, missed, frozen, goal) |
| No setter terms | Setter terms in goal and freeze layers only |
| No sequence / fatigue term | SequenceFatigue (shot index within a defending-skaters-persist sequence) |
| No clock terms | Time-in-period (3 terms); period covered implicitly via sequences |
| No coach terms | Per-head-coach for/against terms per layer |
| No centering penalties | Shot-weighted zero-sum centering via ~10⁶ off-diagonal penalties |
| Single rush indicator | Rush sub-terms by preceding event type (5 categories) |
| Single rebound indicator | Rebound delay by 1–5 s bucket (5 terms) + rebound-shooter identity |
| Rush window ≤4 s | xG8 context window ≤5 s (arbitrary); same "different zone" criterion |
| Rebound window ≤3 s | xG8 rebound is subset of cycle/rush window, classified by delay buckets |
| Person diag penalty 100 (goalie+shooter) | Shooters 0.2, setters 0.2, goalies 30, coaches 1000 |
| Hex diagonal 0.1, fusion constant 5 | Hex diagonal 0.01; fusion count-aware c_pq = 0.2·min(m,n)/√(mn) |
| Rookie prior 0 with λ = 0.001 | Rookie prior ±0.025 logit/shot from 200 (skaters) / 1000 (goalie) imaginary shots |
| 5 shot types | 4 shot types (wrist/snap, slap, backhand, tip; wraparound is a type in xG8 too) |
| Backhand perimeter pooled with same hex fabric | xG8 adds explicit backhand perimeter term for shots outside the backhand fabric |

---

## Feature / covariate list (complete as stated)

- **Shooter identity:** one indicator per shooter (879 in 2019-20)
- **Goaltender identity:** one indicator per goaltender (86 in 2019-20)
- **In-zone shot location:** hex fabric for each of 4 types: wrist/snap (734 hexes), slap (658),
  backhand (433), tip/deflection (184)
- **Wraparound:** single indicator (no hex detail)
- **Below-goal-line:** single indicator
- **Neutral zone (behind blue line):** single indicator
- **Rush:** binary (prev event in different zone ≤4 s)
- **Rebound:** binary (prev event = same-team shot ≤3 s)
- **Score state:** leading; trailing (tied = implicit reference)
- **Strength:** SH; PPv3; PP; 3v3 (EV = 4v4+5v5 = implicit reference)

No clock, no score×period interaction, no zone-start, no setter, no sequence, no coach.

---

## Evaluation protocol and reported results

No systematic held-out evaluation protocol is described in the article. The model is fit sequentially
by season; no train/test split, cross-validation, or calibration metric is reported for the rendered
article text. Reported numbers are illustrative examples from the 2019-20 season fit:

- Goalie result example: Hellebuyck ~−12% odds impact (best), Dubnyk ~+14% (near worst).
- Strength odds ratios as tabulated above.
- Geometric patterns described qualitatively per shot type.

The article notes that covariate values "can be difficult to interpret" but are recoverable as
probability impacts via the logistic function. Historical per-season results are linked but not
described in the article body.

---

## Outputs / artifacts

- Per-season model coefficients: per-shooter, per-goaltender, per-hex, and structural terms.
- Per-shot P(goal) scores (xG) over the full shot population.
- Goaltender, forward, and defender result pages with interactive threshold controls (separate HTML
  pages linked from Player Results; not fetched here).
- Historical per-season coefficient pages (2007-08 through 2018-19 linked; not fetched).

---

## Linked / companion articles

- The predecessor model ("last year's model"): URL not given explicitly; the 5v5+5v4 only version
  that Magnus 3 expands.
- van Wieringen "Lecture notes on ridge regression" (§5): the fitting reference (same document cited
  in xG8).
- Forward and defender result pages (linked as performance-split pages; not fetched).

---

## Open questions / ambiguities

1. **No xG0 description.** This article defines only the full xG model. The xG0 reference model (the
   shot-map display denominator) is NOT introduced here. See §Cross-check.
2. **Hex geometry.** No hex side-length or resolution is stated; only the fabric sizes (shot counts)
   are given. The xG8 write-up (2025) states "88 cm / 2.9 ft sides" for its fabric; whether this was
   the same in 2020 is not stated.
3. **Left/right symmetrization.** The article does not state whether the hex fabrics are
   symmetrized L/R; xG8 explicitly symmetrizes for support.
4. **Score×strength interactions.** Not mentioned; neither adopted nor declined.
5. **Term centering.** No centering or zero-sum constraint mentioned; xG8 adds this later.
6. **Penalty values — unit interpretation.** The goalie/shooter diagonal 100 vs xG8's 30/0.2 is a
   large difference; whether the change reflects a changed model scale (single-outcome vs per-layer)
   or a deliberate shift in talent-spread beliefs is not documented.
7. **Uncertainty estimates reported alongside point estimates.** The text says "fitting this model
   produces both a point estimate and an uncertainty estimate for each covariate"; the uncertainty
   becomes Λ for the next season. The form of this uncertainty (Hessian diagonal? other?) is not
   stated.
8. **Empty-net and penalty-shot exclusion.** "All shots taken at a net with a goalie" implies
   empty-net exclusion. Penalty shots and shootout shots are not mentioned separately; xG8 explicitly
   excludes them.

---

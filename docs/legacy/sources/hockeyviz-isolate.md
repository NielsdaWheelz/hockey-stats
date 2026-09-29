# HockeyViz — How Isolation Works (Isolated Impact Charts)

- **Title (primary):** "How to read Isolated Impact Charts"
- **Author:** Micah Blake McCurdy (HockeyViz, @IneffectiveMath)
- **URLs actually used:**
  - Primary: https://hockeyviz.com/howto/isolate (live page; WebFetch returned HTTP 403, retrieved instead via direct HTTP GET with a browser User-Agent; web.archive.org was unreachable from this environment)
  - Companion 1 (load-bearing 5v5 methodology the primary defers to): https://hockeyviz.com/txt/magnus7EV — "The Magnus Prediction Model, version 7: Estimating Individual Impact on NHL 5v5 Shot Rates", dated August 2, 2023
  - Companion 2 (quantification/common-scale methodology the primary defers to): https://hockeyviz.com/txt/sG — "sG: Synthetic Goals", dated August 3, 2023
- **Accessed:** 2026-07-03
- **2026-07-15 companion refresh:** the dedicated [`Shootiness`](hockeyviz-shootiness.md),
  [`Magnus 9 ST`](hockeyviz-magnus9st.md), and [`Magnus 8 Penalties`](hockeyviz-magnus8p.md)
  dossiers now resolve method details unavailable in this initial three-page review. This dossier
  still records what the dated isolate/Magnus 7/sG pages themselves claimed.
- **Retrieval completeness:** full article text retrieved for all three pages (the primary is short, ~1,000 words; magnus7EV and sG retrieved end-to-end including the Fitting/Computational Details sections). The /txt/sG page's HTML contains a partial duplicate of the magnus7EV text after its "Future Skills" section (apparent template artifact); only the unique sG content is used here.
- **Worked example in the primary:** Auston Matthews chart "as of December 16th, 2024".

## 2. Summary

HockeyViz's "isolation" is not one joint model but a family of separately-fit regressions plus two lighter measurements, whose outputs are composed onto a single player card. The flagship component (Magnus 7) estimates each skater's isolated impact on 5v5 shot rates as a **map over the offensive half-rink**: the units of observation, the regression coefficients, and the published outputs are all shot-rate maps rather than scalars. Observations are "stints" (passages of 5v5 play with no substitutions), each encoded as two rows (home attacking / road attacking); the response is a Gaussian-smoothed (10-ft SD), league-average-centred shot-rate surface, and rows are weighted by stint length. Covariates include per-skater offence/defence terms, coach terms (general, per-score-state, and a third-period "shell"), score state, per-second shift-start-zone terms (4 types × 60 seconds), venue×period, rest patterns, penalty-residual indicators, and a goaltender rebound-tendency term. Fitting is generalized ridge regression with three additive penalty families: a **historical penalty** shrinking each term toward its previous-season estimate (weighted by previous-season precisions), a **structural penalty** shrinking humans toward league average (players 10,000; coaches 100,000; non-human terms 0), and near-hard **pooling penalties** enforcing sum-to-zero constraints in place of reference-category coding. New players get a replacement-level prior (−7.5% offence, +1% defence). Special teams, finishing/setting (a 3-stage logit xG model), penalties, transition ("Ice Won"/"Ice Lost"), and a separately fit Elo-style "shootiness" stat fill out the card. Everything is converted to a common goals scale ("synthetic goals", sG) via a fixed reference basket of 1000 5v5 + 100 PP + 100 PK minutes with league-average context; sG is explicitly a rate-style ability estimate at an instant in time, not a WAR-style descriptive counting stat. Feature inclusion and penalty magnitudes are adjudicated by out-of-sample prediction of future-season shot rates.

## 3. Decision inventory

IDs `hockeyviz-isolate-D#`. Source column: `isolate` = /howto/isolate, `magnus7` = /txt/magnus7EV, `sG` = /txt/sG. Quotes are verbatim (original spellings kept, e.g. "tendancy").

| id | topic | decision | rationale / verbatim quote | article §
|---|---|---|---|---|
| hockeyviz-isolate-D1 | problem framing | The whole enterprise = separate individual ability from teammates, competition, and coach choices; per-aspect impacts, at a moment in time. | "The central task of player analysis is to separate out, as much as possible, the abilities of individual players from the effects of their teammates, their competition, and the choices of their coach." | isolate §intro |
| hockeyviz-isolate-D2 | architecture | Several **separate** regressions, not one joint model: 5v5 shot rates, special-teams shot rates, shooting ability, minor-penalty rates. | "I run several different regressions to estimate player ability: one for impact on shot rates at 5v5, one for special teams shot rates, another for shooting ability, and another for impact on minor penalty rates." | isolate §Overview |
| hockeyviz-isolate-D3 | architecture | The isolate page describes one "largely unregressed" card measure: `Shootiness`, treated as sufficiently individual not to need Magnus-style isolation. The dedicated methodology page clarifies that it is an online Elo-style competitive shooter-share model, not a raw attempt fraction. | The card output is position-relative; resolve exact mechanics through `hockeyviz-shootiness-D1`-`D14`. | isolate §Overview, §Other Things; dedicated Shootiness companion |
| hockeyviz-isolate-D4 | temporal semantics | The chart summarizes ability "at a specific instant in time" — a snapshot estimate, not a season accumulation. | "The point of the isolated impact charts is to summarize the ability of the player… at a specific instant in time." | isolate §intro |
| hockeyviz-isolate-D5 | display hierarchy | 5v5 offence occupies top-left, the "most important place in the viz", because moving the puck into the OZ is deemed the most important skater skill. | "The most important way a skater can affect the results of games is by moving the puck into the offensive zone…" | isolate §5v5 Offence |
| hockeyviz-isolate-D6 | display encoding | 5v5 maps: red = more shots than league average from that location, blue = fewer; special-teams maps use a distinct palette (orange = more, purple = fewer). | "Red areas show where the given player causes shots to be taken at a larger rate than league average, blue areas less." / "Here, orange means more and purple means fewer." | isolate §5v5 Offence, §5v4 |
| hockeyviz-isolate-D7 | attribution stance | Offence map credits the player for teammates' shots caused by his actions, not just his own shots. | "Many of the shots that comprise this offence are taken by him personally, many are taken by his teammates because of his actions all over the ice." | isolate §5v5 Offence |
| hockeyviz-isolate-D8 | 5v5 controls (headline) | 5v5 model controls for teammates, competition, prevailing score, and coach-chosen shift-start zones. | "the short version is that I account for teammates, competition, the prevailing score, and the zones of the ice the coach chooses for the player to begin their shifts in." | isolate §5v5 Defence |
| hockeyviz-isolate-D9 | special teams | A single special-teams model outputs both 5v4 offence and 4v5 defence estimates — necessarily joint because it controls for quality of competition. | "The same model which generates power-play ability estimates also outputs penalty-kill estimates, as it must since it takes quality of competition into account." | isolate §4v5 Defence |
| hockeyviz-isolate-D10 | special teams caveat (author-flagged) | ST estimates are demoted: fewer goals at 5v4, fewer minutes, weaker assumptions; low-minute players shrink to average (and many high-minute ones sit near average too). | "not as important as 5v5 play, since so many fewer goals are scored at 5v4, and the model operates on fewer minutes of data and somewhat more tenuously follows its assumptions." | isolate §5v4 Offence |
| hockeyviz-isolate-D11 | finishing definition | Finishing = shooting ability after conditioning on shot location, shot type, and goaltenders faced; from the shooting & goaltending (xg7) model. | "the shooting ability of the player after taking into account where they shoot from, what types of shots they use, and which goaltenders they face." | isolate §Other Things |
| hockeyviz-isolate-D12 | setting definition | Setting = "the specific sort of passing that immediately precedes shooting" — a measured skill separate from finishing. | (as quoted) | isolate §Other Things |
| hockeyviz-isolate-D13 | penalties definition | Penalties drawn/taken measured as **team-level** non-offsetting minors per minute the skater causes; explicitly distinguished from individual penalties drawn. | "It is possible for a player's indivdual penalties drawn to be quite substantially different from their impact on their team's penalties." | isolate §Other Things |
| hockeyviz-isolate-D14 | transition definition | Transition impact = whether the player leaves the puck in better/worse locations at shift end vs shift start, split into "Ice Won" and "Ice Lost", vs an average player taking the same shifts. | "the way they leave the puck in either better or worse locations at the ends of their shifts compared to the beginnings" | isolate §Other Things |
| hockeyviz-isolate-D15 | common scale | All impacts quantified on one scale via a standard icetime basket: 1000 5v5 + 100 PP + 100 PK minutes with league-average teammates and opponents → "synthetic goals" (sG); per-skill values in the starburst, total in centre. | "a standard 'basket' of icetime of one thousand 5v5 minutes, 100 power-play minutes, and 100 penalty-kill minutes with league average teammates and league average opponents." | isolate §Other Things; sG intro |
| hockeyviz-isolate-D16 | observation target | Shot-rate **maps** are the units of observation AND of the estimates — the key design choice enabling "where" patterns, not just how-much scalars. | "The most important feature of this model is that I use shot rate maps as the units of observation and thus also for the estimates themselves." | magnus7 §Introduction |
| hockeyviz-isolate-D17 | shot definition | "Shot" = NHL-recorded scored, saved, missed, **or blocked** (blocked shots newly included in v7); blocked-shot locations imputed from the block location per xg7's imputation. | "'shot' means an event recorded by the NHL as either scored, saved, missed, or blocked… these locations are inferred from their block location." | magnus7 §Introduction, §What's New |
| hockeyviz-isolate-D18 | row unit | Observation row = "stint": a passage of 5v5 play with no substitutions (may span stoppages/faceoffs); each stint yields two rows, home-attacking and road-attacking, with no non-zero columns in common. | "Each passage of 5v5 play with no substitutions is encoded in the model as two rows" — ~250k stints/season → ~500k rows × ~2k covariates. | magnus7 §Method |
| hockeyviz-isolate-D19 | model class | Weighted linear model \(Y \sim WX\beta\); W diagonal = stint length in seconds, so longer stints weigh more. | "The weighting matrix W, which is diagonal, is filled with the length of the shift in question." | magnus7 §Method, §Response |
| hockeyviz-isolate-D20 | player terms | Two columns per skater: offensive impact (own team's shot rates) and defensive impact (opponent's shot rates). | (as stated) | magnus7 §Covariates |
| hockeyviz-isolate-D21 | coach terms | Per head coach: one general attacking/defending pair; attacking/defending pairs for score states −2,−1,0,+1,+2; plus a "shell" pair applied only when tied or up 1–2 in the 3rd period. Blowouts (±3+) excluded from coach terms. | "I consider 'blowout' states (score differences of three or more) to not be substantially affected by coaching instructions."; shell timing chosen because "score effects are driven primarily by leading teams" (/txt/scoreSeq). | magnus7 §Covariates |
| hockeyviz-isolate-D22 | rest terms | Three rest patterns (well-rested 00 / normal 01 / tired 10), each with offence and defence maps; fractional coding by share of skaters; rare 3-games-in-3-nights coded "10". | "Being well-rested is less beneficial (and more common) than being tired is harmful." | magnus7 §Covariates, §Fatigue |
| hockeyviz-isolate-D23 | score terms | Seven offensive-team score columns: trailing 3+, 2, 1, tied, leading 1, 2, 3+ (distinct from the per-coach score terms). | (as stated) | magnus7 §Covariates |
| hockeyviz-isolate-D24 | zone terms | 240 zone columns: 4 shift-start types (OZ, NZ, DZ, on-the-fly) × 60 per-second terms (seconds 1–60 of the shift) — v7 adds time-since-shift-start. Fractionally coded by share of attacking skaters, spread over applicable seconds; only the ATTACKING team's shift starts enter a row. | "It turns out that the impact of a shift start change substantially over time." | magnus7 §Covariates, §Method example |
| hockeyviz-isolate-D25 | venue/period terms | Six game-time-and-venue columns: home/away × period 1/2/3. | (as stated) | magnus7 §Covariates |
| hockeyviz-isolate-D26 | penalty-residual terms | Two columns for 5v5 play immediately after an expired penalty (before any whistle): one for the formerly-shorthanded team, one for the formerly-advantaged team. | "The shot rates for this 'power-play residual' period are very, very high, even higher than for the bulk of power-plays themselves." | magnus7 §Covariates, §Residuals |
| hockeyviz-isolate-D27 | goalie rebound terms | Defending-goalie rebound tendency encoded by setting the coefficient equal to n = shots in that row's own response — an acknowledged endogeneity hack. | "This pilfering of a scrap of information from the dependent variable to put into the design matrix is not quite orthodox but I don't see a better way to handle rebounds at this time." | magnus7 §Covariates |
| hockeyviz-isolate-D28 | rebound caveat (author-flagged) | Rebound terms improve prediction only slightly and are unstable: year-to-year correlation 0.10; conditioning rebound likelihood on shot type is deferred. | "they are not a particularly stable skill, with a year-to-year correlation of only 0.10." | magnus7 §Rebounds |
| hockeyviz-isolate-D29 | response encoding | Each shot → 2-D Gaussian at NHL (x,y), SD = 10 ft (chosen to dominate location measurement error vs video and to smooth); sum Gaussians, divide by stint seconds, subtract league-average shot rate → excess-rate surface over the offensive half-rink. | "this arbitrary figure is chosen because it is large enough to dominate the measurement error typically observed by comparing video observations with NHL-recorded locations". | magnus7 §Response |
| hockeyviz-isolate-D30 | mean-centring | Responses are centred by subtracting the league-average shot-rate map, so every coefficient reads as "change from league average". | "Finally, I subtract the league average shot rate from this." | magnus7 §Response |
| hockeyviz-isolate-D31 | discretization | Half-rink dissected into a 100×100 grid (10,000 cells, 1 ft × 0.85 ft); the functional regression is computed as 10,000 independent per-cell regressions whose outputs recombine into maps. | "sufficiently coarse to permit efficient computation and sufficiently fine to appear smooth". Claimed novel: "the extension of ridge regression to functions… is new, at least in this context." | magnus7 §Fitting, §Previous Work |
| hockeyviz-isolate-D32 | fitting objective | Generalized ridge regression: minimize \(\|Y-X\beta\|_W^2 + \|\beta-\beta_0\|_\Lambda^2 + \|\beta\|_K^2\); closed form \(\beta = (X^TWX+\Lambda+K)^{-1}(X^TWY+\Lambda\beta_0)\). | "deviation from the given year's data is bad… deviations from our prior estimates β₀ are bad… deviations from zero (that is, from league average) are bad." | magnus7 §Fitting, §Computational Details |
| hockeyviz-isolate-D33 | historical penalty | Fit season-by-season from 2007-08 onward; β₀ = previous season's β; Λ diagonal = previous season's estimated precisions. Ability assumed slowly-varying, so old information is downweighted but never discarded. | "I take the opinion that our estimates ought to change slowly, since a player's athletic ability also usually changes slowly." | magnus7 §Historical penalty |
| hockeyviz-isolate-D34 | season unit | Single seasons as the fitting unit; pairs-of-seasons tested and **discarded** for this model (helped the xG model, hurt future-season shot-rate prediction here). | "I considered using pairs of seasons to estimate player ability; this improved my xG model but does not help here, so I've continued to use single seasons." | magnus7 §What's New |
| hockeyviz-isolate-D35 | new-player prior | Players absent last season get a replacement-level prior: −7.5% of league baseline offence, +1% defence; derived by iterating a rank-based replacement definition (below 13n forwards / 7n defenders by icetime) to a fixed point. Also used for everyone in 2007-08. | "It is not usually my habit to implicitly trust coaching staffs even to this very mild extent, but it seems unavoidable here." | magnus7 §Historical penalty |
| hockeyviz-isolate-D36 | structural player penalty | Player ridge-to-zero penalty K = 10,000, set by rough out-of-sample testing; theoretically "optimal" (GCV) values rejected as producing unstable estimates. | GCV-style estimates "suggest much smaller values which give wildly varying (and hence unphysical) year-to-year estimates of player ability." | magnus7 §Player penalties |
| hockeyviz-isolate-D37 | prior-centring cheat (author-flagged) | League-average centring uses the current season's average rather than the prior season's — an acknowledged small violation of prior discipline. | "A truly disciplined modeller would have used the league average from the previous year… I have cheated slightly and used the data from the season at hand instead." | magnus7 §Player penalties |
| hockeyviz-isolate-D38 | fusion prior | Identical twins (the Sedins) fused with a similarity penalty of weight 10,000; no more-distant relation qualifies. | "I have chosen to fuse the Sedins in this way… because they are twins. I don't consider any more-distant relation than twins as legitimate grounds for this kind of prior." | magnus7 §Player penalties |
| hockeyviz-isolate-D39 | coach penalty | Coach terms penalized at 100,000 — 10× tighter than players; a reversion adopted because out-of-sample testing favors a much tighter range of coach impacts. | "to my surprise out-of-sample testing shows that better predictions are obtained with a much tighter range of coaching impacts." | magnus7 §Coaching penalties |
| hockeyviz-isolate-D40 | non-human penalty | Score, zone, rest, venue-period terms get penalty 0 (OLS-like): not theoretically constrained, and data support is large enough that overfitting isn't expected. | "for all of the terms that measure the impact of a thing that is not a human… I use a penalty value of 0." | magnus7 §Non-human penalties |
| hockeyviz-isolate-D41 | identifiability via pooling | Sum-to-zero constraints implemented as near-hard quadratic "pooling penalties" (weights "a million times larger" than the 10,000 scale) instead of reference-category coding: zone, score, rest, venue-period terms each sum to zero; all coach terms sum to zero; each coach's score-specific terms sum to zero. | Preference for interpreting each term "as I would strongly prefer, as 'change from average'" rather than "change from an on-the-fly shift"; "deviations from the desired sums are contradictions in terms." | magnus7 §Pooling penalties |
| hockeyviz-isolate-D42 | no position terms | No covariates identify player position — deliberately, so positional differences remain measurable in the outputs (F vs D densities compared post hoc). | "I don't include any terms in the model itself that identify players by position, since I would like to be able to measure differences between positions." | magnus7 §Player Marginals |
| hockeyviz-isolate-D43 | QoT/QoC as derived quantities | Teammate quality = icetime-weighted sum of teammates' isolates × 4; competition quality = head-to-head-icetime-weighted sum of opponents' isolates × 5. Computed **after** fitting, from the player marginals. | "multiply it by four (since every player has four teammates at 5v5)" / "multiply by five, since every player has five opponents at 5v5." | magnus7 §Teammate/Opponent Impact |
| hockeyviz-isolate-D44 | goodness of fit | Player-level "residuals" (raw on-ice results minus model expectation given observed context) used as a goodness-of-fit display; roughly circular cloud read as encouraging. | "This makes a sort of 'goodness of fit' measure. The obviously circular shape is encouraging." | magnus7 §"Residuals" |
| hockeyviz-isolate-D45 | coach aggregation | "Synthetic" total coach impact = overall system term + 0.2 × shell term, because ~20% of the game is played in shell states. | (as stated) | magnus7 §Coach Impact |
| hockeyviz-isolate-D46 | relative-importance findings | On a common scale: teammate effects ≫ competition effects; season-aggregate score effects "surprisingly small—almost negligible"; zone effects smaller than competition; coach-system effects ≈ competition; fatigue "incredibly tiny" (not even plottable). | "By focussing on only offensive zone faceoffs and defensive zone faceoffs, as some analyses do, small differences between contexts can appear heavily inflated." | magnus7 §Relative Scale |
| hockeyviz-isolate-D47 | evaluation criterion | Out-of-sample prediction of **future-season shot rates** is the umpire for feature inclusion and penalty magnitudes (used to discard season-pairs, set K≈10,000, tighten coach penalty, keep rebound terms). | "this summer I tested a number of promising ideas which turn out to make the prediction of future-season shot rates worse, so they have been discarded." | magnus7 §What's New, §Fitting |
| hockeyviz-isolate-D48 | sG isolation principle | sG values intrinsic ability only, excluding everything outside player control — including minutes played, which is a coaching choice; hence a fixed basket rather than observed TOI. | "vitally, minutes played, since playing time is determined by (somewhat constrained) coaching choices, and is not in any player's ability to affect." | sG intro |
| hockeyviz-isolate-D49 | sG semantics | sG is a rate stat and a point-in-time ability estimate — explicitly NOT a WAR/GAR-style descriptive counting stat divvying up credit for past goals. | "sG is not descriptive of the past… it is an estimate of ability at a given moment in time… not a counting stat; it is instead a rate stat." | sG intro |
| hockeyviz-isolate-D50 | sG shot-rate conversion | 5v5/PP/PK shot-rate impacts convert to goals as (isolated xG per hour) × basket minutes, assuming league-average shooters, setters, goaltenders (5v5: ×1000 min; PP/PK: ×100 min each). | Crosby example: 0.31 xG/hr → 5.17 sG over 1000 5v5 minutes. | sG §5v5 / §PP&PK |
| hockeyviz-isolate-D51 | sG finishing/setting machinery | xG model gives per-player logit-scale impacts at 3 stages (unblocked; on-net given unblocked; goal given on-net); apply to an empirical 2018–2023 shot distribution (discretized 3-D configuration space); per-shot Δ = p'ᵦp'ₘp'ᵍ − pᵦpₘpᵍ; scale by 0.94 shots/min (all-situations) × 1200 min; role shares: shooter 2/9 for forwards (F take ⅔ of shots, 3 F on ice); setting: 80% of shots have setters, 7/9 forwards. | (as stated, Crosby worked example: +2.6 sG shooting, +3.5 sG setting) | sG §Finishing and Setting |
| hockeyviz-isolate-D52 | sG penalty valuation | A drawn penalty ≈ +0.207 net goals (5v4 goal prob 24.0% vs 5v5 8.5% offensively, +4v5 3.3% vs 8.5% defensively); penalty-model outputs (per 1000 all-situation min) × 0.207 × 1200/1000. | "drawing a penalty has an offensive value of 24.0% − 8.5% = +0.155 goals for and a defensive value of 3.3% − 8.5% = −0.052 goals against, for a net benefit of 0.207 goals." | sG §Penalties |
| hockeyviz-isolate-D53 | sG synergy exclusion (author-flagged) | Skill contributions kept strictly separate; creator-who-also-finishes synergy (extra created shots taken by the creator himself) deliberately excluded "for reasons of complexity", may be added later. | "I've decided not to include these 'synergy' effects at the moment, for reasons of complexity." | sG §Synergy |
| hockeyviz-isolate-D54 | sG extensibility rule | New skills may be added to sG as long as they are "reasonably independent of one another"; transition (territory won/lost per shift) was in preparation at writing (Aug 2023) and appears on the current card; goalie and coach sG planned. | "As long as skills are reasonably independent of one another, they can be added to a player's sG." | sG §Future Skills |
| hockeyviz-isolate-D55 | access model | Research/methodology public; the specific per-player and per-coach regression outputs are subscriber-gated. | "I restrict access to the specific regression outputs for players and coaches to website subscribers." | magnus7 §Player and Coach Results |

## 4. Model structure sketch

Composition on the isolated-impact card (each box fit separately; sG composes them):

```
                         ┌────────────────────────────────────────────────┐
                         │ Isolated Impact Chart (per player, per instant)│
                         └────────────────────────────────────────────────┘
   5v5 maps (top/bottom-left)      ST maps (top/bottom-right)      centre starburst + distributions
        │                                │                                │
  Magnus 7 (magnus7EV)          Special-teams model            xg7 (finishing, setting logits;
  5v5 shot-rate MAP regression  (magnus6ST): PP-off + PK-def   goalies faced conditioned on)
        │                        jointly (QoC forces joint)     Penalty model (magnus6P):
        │                                                       team minors drawn/taken /min
        │                                                       Transition: Ice Won / Ice Lost
        │                                                       Shootiness: Elo-style, position-relative
        ▼
  Magnus 7 internals:
  stints (no-substitution 5v5 passages) → 2 rows each (home-atk / road-atk)
  response Y: Σ 10-ft Gaussians at shot (x,y) ÷ stint seconds − league-average map
  design X: player-off/def | coach general/score-state/shell | score(7) |
            zone (4 types × 60 per-second terms, attacking team only) |
            venue×period(6) | rest(3×off/def) | penalty-residual(2) |
            goalie-rebound (defending side, coefficient = n shots in own response)
  fit: generalized ridge over a 100×100 grid (10,000 per-cell regressions):
       min ‖Y−Xβ‖²_W + ‖β−β₀‖²_Λ (historical: prior season, precision-weighted)
                      + ‖β‖²_K   (structural: players 10k, coaches 100k, twins-fusion 10k,
                                   non-human 0, pooling sum-to-zero ~10⁶× stronger)
  β = (XᵀWX+Λ+K)⁻¹(XᵀWY+Λβ₀);   iterated season-by-season since 2007-08
        │
        ▼
  derived post-fit: QoT (Σ teammate isolates, TOI-weighted, ×4), QoC (×5),
  player "residuals" (raw − model-expected), coach synthetic (= overall + 0.2·shell)
        │
        ▼
  sG layer: every skill → goals over a fixed basket (1000 5v5 + 100 PP + 100 PK min,
  league-average context); finishing/setting via 3-stage logit shift over the
  2018–23 shot distribution; penalties via ×0.207; total sG at card centre
```

Conditioning notes: player 5v5 terms are estimated jointly with (and therefore conditioned on) teammates, opponents, score, coach terms, zone-time terms, venue/period, rest, penalty residuals, and goalie rebound tendency — all within one ridge solve. The special-teams and penalty models are separate solves. Nothing in Magnus conditions on position (hockeyviz-isolate-D42). sG conditions on nothing observed — it fixes context at league average by construction.

## 5. Full feature/covariate list (Magnus 7, as stated)

Paired offence/defence terms:
- Player performance: 2 columns per skater (offensive impact on own team's shot rates; defensive impact on opponents').
- Coach impacts, per head coach: 1 general attacking/defending pair; attacking/defending indicator pairs for score states trailing-by-2, trailing-by-1, tied, leading-by-1, leading-by-2 (no blowout terms); 1 attacking/defending "shell" pair active only when tied or leading by 1–2 in third periods.
- Rest impacts: "well rested" (00), "normal" (01), "tired" (10), each with an offence and a defence map; fractional coding by share of skaters; 3-in-3 players coded 10.

Offensive-team-only terms:
- Score impacts: 7 columns (trailing 3+, trailing 2, trailing 1, tied, leading 1, leading 2, leading 3+).
- Zone impacts: 240 columns = {OZ, NZ, DZ, on-the-fly} × seconds 1–60 of the shift; coefficients fractional by share of attacking skaters and spread evenly over applicable seconds; defenders' shift starts not considered in that row.
- Game time and venue: 6 columns = {home, away} × {1st, 2nd, 3rd period}.
- Penalty residuals: 2 columns (formerly-shorthanded team; formerly-advantaged team), for post-expiry pre-whistle 5v5.

Defensive-team-only terms:
- Goaltender rebound tendency: per-goalie column with coefficient n = number of shots in that row's response.

Scale: ~2,000 covariates total; ~500,000 rows per season.

(The isolate card additionally draws on the special-teams model, xg7 finishing/setting, the penalty
model, transition, and shootiness. The exact current-version ST, penalty, and shootiness methods are now
covered by the 2026-07-15 companion dossiers linked in the metadata above; finishing conditions on shot
location, shot type, and goaltender faced per hockeyviz-isolate-D11.)

## 6. Evaluation protocol and reported results

- **Protocol:** out-of-sample prediction of *future-season shot rates* is the stated criterion for feature inclusion and penalty calibration (hockeyviz-isolate-D47). Applications reported: season-pairs discarded (worsened prediction here despite helping xG); player structural penalty ≈10,000 validated by "rough out-of-sample testing"; GCV-derived penalties rejected as unstable; coach penalty tightened to 100,000 because it predicts better; rebound terms retained because they "improve the prediction accuracy of the shot rate model slightly".
- **Goodness of fit:** player-level residual plot (raw on-ice minus model expectation) is "obviously circular", read as encouraging (hockeyviz-isolate-D44). No numeric R²/likelihood/calibration metrics are reported in the fetched text.
- **Stability:** goalie rebound tendency year-to-year correlation = 0.10 (flagged weak).
- **Substantive results reported:** home advantage in every period; 2nd-period shot uptick; 3rd-period decline net of score; trailing teams dominate play; tied states "cagey"; OZ starts boost offence with steady decay; DZ and NZ starts similarly depress offence (the binding obstacle is the opponent's blue line); on-the-fly shifts productive early then decay; power-play and penalty-kill residual stints both have elevated shot rates; teammate variation ≫ competition variation; season-scale score and zone effects small; coach effects ≈ competition; fatigue negligible; forwards generate more offence than defenders; TOI-weighted averages skew good (coaches play their better players).
- **Worked player example:** Taylor Hall (NJ 16-18): raw on-ice +7.3%/−6.3%; isolated +13.3% offence, −12.9% defence; teammates −1.3%/+10.5%; opponents +0.1%/+5.4% — "personally driving the play… in the teeth of weak teammates and tough opponents."

## 7. Outputs / artifacts

- **Player isolated impact chart** (the primary artifact): four rink maps (5v5 offence top-left, 5v5 defence bottom-left, 5v4 offence top-right, 4v5 defence bottom-right); centre starburst with per-skill sG values and total sG; distribution strips for finishing, setting, penalties drawn, penalties taken; shootiness value; Ice Won / Ice Lost transition values.
- **Per-term maps** from Magnus: game-state (venue×period), score-state, rest, 240 zone-second maps (also animated GIF), penalty-residual maps, goalie rebound maps — each annotated with a neutral-zone xG-rate-vs-baseline % figure (e.g. "+16.6% xG/60").
- **Density scatter distributions** (offence vs inverted defence axes, "GOOD" corner marked, decile contours, TOI-weighted red dot + unweighted black dot): raw on-ice, player marginals (all/F/D), teammate impact, opponent impact, combined, score, zone, coach, residuals, and a common-scale "sixfold" comparison.
- **Coach artifacts:** overall-term scatter, shell-term scatter, synthetic (overall + 0.2×shell) scatter; subscriber coaching pages.
- **Numbers:** per-skill sG and total sG per player; per-term xG% impacts. Player/coach regression outputs subscriber-gated on player career pages and /coaches.

## 8. Linked / companion articles referenced

Fetched as companions (the 2 allowed):
- https://hockeyviz.com/txt/magnus7EV — Magnus 7, 5v5 shot-rate model (load-bearing methodology; fetched, distilled above)
- https://hockeyviz.com/txt/sG — Synthetic Goals (quantification; fetched, distilled above)

Referenced, NOT fetched:
- https://hockeyviz.com/howto/shotMap — how shot-rate maps encode xG in pictures (covered by sibling agent)
- https://hockeyviz.com/txt/xg7 — shooting & goaltending (xG) model; also owns the blocked-shot location imputation (…/txt/xg7#blockedShotLocationImputation)
- https://hockeyviz.com/txt/magnus6ST — special-teams shot-rate model (per sG's model list)
- https://hockeyviz.com/txt/magnus6P — penalty model (per sG's model list)
- https://hockeyviz.com/txt/magnus6EV — Magnus 6 (predecessor)
- https://hockeyviz.com/txt/scoreSeq — "score effects are driven primarily by leading teams" (shell-term justification)
- https://hockeyviz.com/txt/shifts1 — why on-the-fly shifts can't be broken down by location
- External: Brian MacDonald 2012, https://arxiv.org/pdf/1201.0317.pdf (first regularized regression in hockey; GCV §5.3); Schuckers & Curro THoR, http://statsportsconsulting.com/main/wp-content/uploads/Schuckers_Curro_MIT_Sloan_THoR.pdf; van Wieringen, generalized ridge lecture notes, https://arxiv.org/pdf/1509.09169.pdf; Evolving-Hockey (https://evolving-hockey.com/) and the defunct Corsica (WAR lineage; replacement-level method credited to the Younggrens).

## 9. Open questions / ambiguities in the source

1. **Shootiness wording tension (resolved mechanically):** the isolate page calls the measure "largely
   unregressed", while the dedicated source documents a competitive Elo-style update over the full on-ice
   set. The latter owns the formula; the former is retained only as loose card/product wording. The
   dedicated source still leaves its probability-versus-rating display baseline ambiguous.
2. **Transition methodology:** "Ice Won"/"Ice Lost" appears on the current card (Matthews, Dec 2024) but the fetched sG page (Aug 2023) still lists the territory model as "in preparation"; how transition is measured and converted to sG is not documented in the fetched pages.
3. **Version drift across the card lineage:** this 2023 isolate/sG snapshot points to Magnus 6 ST and
   Penalties, while the refreshed corpus documents Magnus 9 ST and Magnus 8 Penalties. Current-method
   details must come from those newer dossiers; the older card's exact historical component values must
   not be silently recomputed under the newer definitions.
4. **Λ "estimated precisions":** how per-term precisions are extracted from a prior season's ridge fit (posterior covariance? which formula?) is not specified. (inferred: diagonal of the ridge posterior precision, but the text doesn't say.)
5. **Pooling penalty magnitude:** "multiplied by an extremely strong factor (a million times larger than the 10,000 penalty for the coaches and players above)" — ambiguous between ~10⁶ and 10⁶×10⁴=10¹⁰, and it also calls 10,000 the penalty "for the coaches" though coaches were said to be 100,000.
6. **OLS formula typo:** the text writes β = (XᵀX)⁻¹XᵀWY for the weighted OLS baseline (missing W in the Gram matrix); the later ridge closed form correctly uses XᵀWX. Presumed typo.
7. **Goalie rebound endogeneity:** the response count n is placed in the design row (hockeyviz-isolate-D27); the author flags it as "not quite orthodox" but there is no analysis of the bias this induces on other coefficients.
8. **Per-cell independence:** fitting 10,000 per-cell regressions treats cells independently apart from the input Gaussian smoothing; no cross-cell smoothness penalty on β itself is described — spatial coherence of the coefficient maps comes only from the smoothed responses. (inferred from §Fitting.)
9. **Uncertainty on outputs:** no intervals/credible bands are reported for player maps or sG values in the fetched text; the Bayesian interpretation of the penalties is noted historically but not exploited for uncertainty quantification.
10. **Score vs coach-score collinearity:** global score terms coexist with per-coach score-state terms; identification rests on the per-coach sum-to-zero pooling constraints, but the degree to which league-wide score effects vs coach deviations are separable is not quantified.
11. **sG role-share constants:** the ⅔-of-shots-by-forwards, 80%-of-shots-have-setters, and 7/9-setter-forward shares are asserted "in line with recent tendencies" without citation; per-player shooter-likelihood weighting is explicitly deferred.
12. **"Mediant" league average:** the structural penalty centres on "league average (that is, mediant) shot rate" — the intended meaning of "mediant" (median? weighted mean?) is unclear.
13. **Weighting of the response division:** responses divide by stint seconds and rows are re-weighted by stint seconds; the interaction (rate observation + length weight ≈ count information) is implied but never discussed as a variance model; there is no stated observation-noise model at all.

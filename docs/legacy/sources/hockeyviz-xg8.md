# HockeyViz — "Magnus 8: xG" (xG8, layered expected goals)

- **Title (as published):** "Magnus 8: xG — Shooting, Setting, and Goaltending"
- **Author:** Micah Blake McCurdy (@IneffectiveMath)
- **Published:** May 26, 2025
- **URL used:** https://hockeyviz.com/txt/xg8 (fetched directly via curl with a browser user-agent; the WebFetch tool got HTTP 403 from hockeyviz.com). Accessed 2026-07-03.
- **Retrieval status:** Full article text retrieved (from title through Thanks/copyright, including all three technical appendixes). Figures/plots referenced in the article were not retrieved (they are PNGs); everything below is from the article's prose.
- **Scope note:** Report contains ONLY what the source says. Inferences are marked "(inferred)". A few notes reference content that exists in the page's HTML source but is commented out (i.e., NOT rendered); these are explicitly flagged as non-rendered remnants and not attributed to xG8.

## 2. Summary

xG8 is the eighth major version of McCurdy's expected-goals model, fit on NHL play-by-play from 2007-08 through the present, one season at a time, with each season's estimates carried forward as priors for the next. Instead of a single P(goal | shot) model, it is a stack of four sequential conditional logistic regressions — the "layers": P(at net vs blocked), P(on net vs missed | unblocked), P(in play vs frozen | on net), and P(goal vs rebound/save | on net and not frozen) — and the shot's xG is the product of the four success probabilities. Every layer shares the same GLM-in-logits shape and (mostly) the same covariate families: strength state, region + shot-type-specific hexagonal location fabrics, 5-second previous-event context (open play / cycle / rush with sub-terms, rebound delay and rebound-shooter terms), time-in-period, score state, a new shot-"sequence" fatigue proxy, and person terms for shooters, setters (pass-before-shot, imputed when no goal), goaltenders, and head coaches (for and against). Fitting is penalized maximum likelihood with generalized ridge penalties: near-zero penalties on structural terms, hand-tuned diagonal penalties on person terms (0.2 shooters/setters, 30 goalies, 1000 coaches), shot-count-driven fusion penalties smoothing adjacent hexes, huge "centering" penalties forcing each term family to shot-weighted zero mean, and dynamic season-to-season penalties anchoring each person to their prior-year estimate (strength 5·√(prior shots), with explicit "rookie priors"). New in v8 versus v7: the old on-net-vs-goal layer is split in two so goalie freezes are a first-class outcome, rush/cycle shots get more detailed sub-structure, and fitting returns to single seasons instead of two-year windows. The article also documents rejected ideas (score×rush/cycle interactions, location-specific shooter/goalie skill, diffuse per-player on-ice shot-quality effects) and reports weak cross-correlations between the layer skills plus high year-over-year stability. Evaluation is out-of-sample predictive comparison used as a term-admission gate; no single headline accuracy metric for v8 is reported in the rendered article.

## 3. Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| hockeyviz-xg8-D1 | Layer decomposition | Four sequential conditional submodels: blocked→at-net, missed→on-net, frozen→in-play, saved/rebound→goal; xG = p_at·p_on·p_in·p_go | "together they form 'an xG model', I call the submodels the 'layers' of the model although they are each, strictly speaking, a model in their own right" | Estimating Shot Outcomes |
| hockeyviz-xg8-D2 | v8 change: freeze layer | Split the previous "on net vs goal" layer into frozen-vs-in-play and in-play-vs-goal, "to let us look at freezes as first-class results" | Primary motivation stated later: "to better describe goaltenders" | Estimating Shot Outcomes; Goaltending |
| hockeyviz-xg8-D3 | v8 change: rush/cycle | Reworked rush and cycle shot treatment "with more detail for both kinds of shots" (sub-terms by preceding event type, rebound delay, rebound shooter) | listed as a new aspect of v8 | Estimating Shot Outcomes |
| hockeyviz-xg8-D4 | v8 change: fit window | "Returning to single-season fittings instead of two years at a time" | (no further rationale given) | Estimating Shot Outcomes |
| hockeyviz-xg8-D5 | Shot definition | "Shot" = any shot attempt (not just on goal); conceptually frozen "at the moment when the puck leaves the stick", before the outcome is known | conceptual clarity about the object being modeled | Vital Theoretical Preliminaries |
| hockeyviz-xg8-D6 | Exclusions | Shots against teams with no goalie on the ice, and shots with no skaters on ice (penalty shots, shootouts), are excluded entirely | empty-net shots "cannot be thought of as a contest between shooter and goaltender ... they would serve no purpose" | Preliminaries; Extra Attacker Shots |
| hockeyviz-xg8-D7 | Model class | Logistic regression (GLM, logit link) for every layer; all effects additive in logits; positive = more likely to "succeed" at that layer | probabilities are inconvenient to fit directly; logits allow unrestricted additive terms | Probability In Regression |
| hockeyviz-xg8-D8 | Frozen outcome definition | Shots deflected by the goalie out of play are counted as "frozen" | (definitional convenience; no other rationale) | Probability In Regression |
| hockeyviz-xg8-D9 | Base rates (constants) | Constant terms per layer, 2024-25: ~80% at-net (~+1.5 logits), ~2/3 on-net (~+1 logit), ~25% of on-net frozen, ~8-9% of unfrozen on-net scored (~−2.2 logits) | constants anchor the logit scale for all other terms | Probability In Regression; Results |
| hockeyviz-xg8-D10 | Display encoding of terms | Non-constant terms shown not in raw logits but as probability-of-success impact relative to constant-only, scaled by 100 | readability of tables/plots | Even Strength Shots |
| hockeyviz-xg8-D11 | Proxy philosophy | Many terms are explicit proxies for unobserved microstructure (defender positions, puck trajectory); he would drop proxies if tracking data existed | "we craftily attempt to gain exposure to the things we do not have through the things that we do" | Skater Strength |
| hockeyviz-xg8-D12 | Strength states | Terms: EV (5v5 pooled with 4v4), 3v3 (own term, "so different in style"), EA (extra attacker), PP, SH, PPv3 (5v3 and 4v3) — per layer | mechanism: bodies in shooting/passing lanes; PPv3 shots "are the highest quality shots in the game, structurally" | Skater Strength |
| hockeyviz-xg8-D13 | Centring | Every categorical family is "centred": shot-weighted sum of terms = 0, so each term reads as impact vs an average shot; enforced via penalty (see D44) | "the sum of these terms, weighted by how many shots are in each category, is zero in each submodel" | Skater Strength; Centering Penalties |
| hockeyviz-xg8-D14 | Region partition | First split: below goal line; beyond the nearest blue line (distant); remainder = in-zone | below-goal-line shots rarely blocked; distant shots' on-net rate is confounded: wide ones become unrecorded "dump-ins" (author flags this) | Regions of the Ice |
| hockeyviz-xg8-D15 | Shot-type fabrics | In-zone shots split into 4 shot-type categories with separate spatial treatment: wrist/snap (also absorbing cradle/"michigan", bat, poke, wraparound), slap, tip/deflection, backhand | geometry of shot success depends strongly on shot type — credited to Michael Schuckers | Regions of the Ice / In-zone Shots |
| hockeyviz-xg8-D16 | Hex resolution | Hexagonal fabric with 88 cm / 2.9 ft sides (~2 m² per hex; "fairly coarse"); nearest-hex assignment | "partially for computational efficiency, partly for simplicity, and partly for ... 'data honesty'" — league locations only reliable to about this accuracy; previous smaller hexes were not supportable | Specific Shot Locations |
| hockeyviz-xg8-D17 | L/R symmetrization | Fabric artificially symmetrized across the split line; shots from both sides pooled | "the improved data support and smoothness is why I did it, but if there are non-trivial left-right disparities at the league level I will not discern them" | Specific Shot Locations |
| hockeyviz-xg8-D18 | Location dominance; anti-single-model argument | Hex terms span ~±2.5 logits — largest of any common term — and geometric patterns vary by layer within each shot type; a single-outcome xG model "has no way to avoid smushing all this geometric variation together" | he notes his own pre-2023-24 models were single-model; 16 fabrics = 4 shot types × 4 layers, each centred | Specific Shot Locations |
| hockeyviz-xg8-D19 | Tip fabric + tip location imputation | Tips use a restricted fabric (faceoff dot to faceoff dot, out to the top of the slot). Tips recorded outside it get an imputed location: moved 4/5 of the way toward the far post (or, if on the split line, 4/5 toward the middle of the goal line) | league often leaves the ORIGINAL shot's location on plays re-labeled as tips; "This surgery, however unpleasant, seems to match the games I've checked considerably more closely" | Tips and Deflections |
| hockeyviz-xg8-D20 | Tip recording-bias caveat | Author flags that edge-of-fabric tips that miss are likely often simply unrecorded (scorer salience bias), inflating their apparent on-net rate | "a natural but regrettable tendency for scorers (who are humans after all) to notice tips more when they are more salient" | Tips and Deflections |
| hockeyviz-xg8-D21 | Backhand perimeter | Backhands get a small fabric; backhands outside it are pooled into a "perimeter" term | "I do not consider them to be serious attempts to score" | Backhands |
| hockeyviz-xg8-D22 | Blocked-shot origin imputation | League records the BLOCK location, not the shot origin; origin imputed as a probability distribution over hexes farther from the net than the block point, score = exp(−s²/30)·exp(−d²/20) (d = hex-to-block distance, s = off-centre distance where the hex→block line crosses the goal line), normalized | chance proportional to proximity ("most shot blocks are caused by proximity pressure") and to how "on line" the implied shot is | Blocked Shot Trickery; appendix: Blocked Shot Location Imputation |
| hockeyviz-xg8-D23 | Context window | Fixed 5-second "recent context" window (author: "arbitrarily"); no PBP event in window → "open play" (~70% of shots); event in the defending goalie's zone → "cycle" (~25%); event outside that zone → "rush" (~5%) | pre-shot events proxy player/goalie positioning and pressure | Previous Events |
| hockeyviz-xg8-D24 | Cycle sub-terms | Cycle shots get 6 additional centred terms by preceding event type: previous shot, turnover, hit thrown, hit taken, faceoff won, faceoff lost — additive on top of the "cycle" term | preceding event type proxies positioning; e.g. after lost defensive faceoffs defenders "do a good job of getting into shooting lanes" | Cycle Shots |
| hockeyviz-xg8-D25 | Turnover pooling | Giveaways and takeaways pooled into one "turnover" category | "I do not trust the distinction" | Cycle Shots |
| hockeyviz-xg8-D26 | Rebound delay buckets | Rebounds (shot-after-shot) get five terms, one per possible second of delay (1–5 s); centred | delay "makes a surprising difference": bang-bang rebounds now scored less / frozen less; 3–4 s delays scored more / frozen more (recent seasons) | Rebound Delays |
| hockeyviz-xg8-D27 | Rebound shooter identity | Term pair: rebound taken by the same shooter vs a teammate; centred | suggested by Cody Magnusson; teammate rebounds historically more successful (trend recently reversing) | Rebound Shooters |
| hockeyviz-xg8-D28 | Rush sub-terms | Rush shots get 5 terms by preceding out-of-zone event: previous shot, turnover, hit thrown, hit taken, faceoff | turnover- and hit-taken-precipitated rushes carry higher goal chance | Rush Shots |
| hockeyviz-xg8-D29 | Time-in-period | Three centred terms: first minute / middle / final minute of period; per-minute (18-term) version tested and rejected | "Dividing the 'middle' term into eighteen per-minute terms does not improve prediction accuracy, so I have kept them consolidated" | Time-In-Period |
| hockeyviz-xg8-D30 | Score effects | Centred terms: leading/tied/trailing × period (9), plus "garbage time" = score difference ≥5 in P1, ≥4 in P2, ≥3 in P3 | score affects shot rates, so plausibly per-shot outcomes; findings: leading teams' shots blocked less, scored more in P2/P3 | Score Effects |
| hockeyviz-xg8-D31 | Sequences (fatigue proxy) | NEW concept: a "sequence" starts when a team shoots and persists while ≥1 defending skater remains on ice (no time limit); shots indexed 1/2/3/4+ (centred terms) | previous time-in-shift fatigue proxies "have been of no use"; late-sequence shots recently scored more despite failing more at other layers | Sequences |
| hockeyviz-xg8-D32 | Shooter terms | Per-shooter terms per layer (blocked, missed, scored — see Open Questions on freeze layer), centred over the whole league; NO team terms anywhere in the model | "I do not include teams in the model in any way"; best goal-layer shooters right-skewed, nearly all forwards | Shooters |
| hockeyviz-xg8-D33 | No shooter identity on tips | Shooter identities are NOT used for tip/deflection shots; omission improves prediction | "suggests that the few players ... well-known for tipping the puck well are exceptional rather than simply at one end of a skill distribution" | Shooters |
| hockeyviz-xg8-D34 | Setter terms (layers) | "Setting" = the threatening final pass before a shot (term borrowed from volleyball); setter terms included ONLY in the freeze and goal layers; dropped from block and miss layers | adding setters to block/miss layers "increases their predictive power on out-of-sample shots by such a small amount" that dropping ~1000 terms was better | Setters |
| hockeyviz-xg8-D35 | Setter imputation | Goals: recorded primary assister = setter. Non-goals: probabilistic superposition over on-ice teammates — for a forward's shot, each other forward 2× as likely as each defender; for a defender's shot, forwards 3× vs the other defender; all probabilities ×80% (~20% of non-goal shots unassisted). Fractional values in the design matrix | proportions measured from Corey Sznajder's hand-tracked shot-assist data; indicator columns reinterpreted as role probabilities | Setters; appendix: Setter Imputation |
| hockeyviz-xg8-D36 | Setter imputation asymmetry caveat | Author flags the imputation "assigns credit for shots that are scored more precisely and assigns blame for shots that are saved more diffusely", accentuating right-skew | honesty caveat on the setter distribution shape | Setters |
| hockeyviz-xg8-D37 | Goalie terms | No goalie term in the block layer ("goaltenders don't exert any influence ... on whether or not the skaters on their team block shots"); goalie terms in miss, freeze, and goal layers | miss-forcing judged a "real" skill (improves prediction, mildly repeatable) but nearly uncorrelated with goal prevention | Goaltending |
| hockeyviz-xg8-D38 | Implicit danger weighting | Logit-scale fitting implicitly weights shots with success probability near 50% most heavily — i.e., high-danger (~20-30%) chances dominate goalie estimates | "high-danger shots allow more latitude to perceive a goaltender's skill ... routine shots reveal very little that we do not already know" | Goaltending |
| hockeyviz-xg8-D39 | Coach terms | Two centred terms per head coach per layer: impact on own team's shots and on opponents' shots; labeled by head coach but meant to encapsulate the full staff's schemes/deployment | coaches control results only indirectly (schemes, line combos, icetime allocation as behaviour control) | Coaches |
| hockeyviz-xg8-D40 | Fitting objective | Penalized MLE: maximize 𝓛 − βᵀKβ − (β−β₀)ᵀΛ(β−β₀), where K = static (generalized ridge + fusion + centering) penalties and Λ,β₀ = dynamic prior penalties | penalties "encode our prior knowledge about the terms of the model before we consider the data at hand" | Fitting; Computational Delicacies |
| hockeyviz-xg8-D41 | Solver | Iterative reweighted update (van Wieringen §5.2 variant); explicit update formula given; in practice solves the equivalent linear system (no matrix inversion) for speed; step sizes artificially muted to stop oscillation | convergence guaranteed if XᵀWX + Λ + K is PSD, "which it is" | Computational Delicacies |
| hockeyviz-xg8-D42 | Static penalties: structural terms | Non-human terms entirely UNPENALIZED except: rush/cycle preceding-event-type terms (penalty 2) and hex location terms (penalty 0.01) | small penalties only to guarantee convergence under sparse cells (e.g. 2008-09: exactly 100 rush-after-faceoff shots, zero scored) | Static penalties |
| hockeyviz-xg8-D43 | Static penalties: person terms | Diagonal ridge penalties: shooters 0.2, setters 0.2, goalies 30, coaches 1000 (both directions) | "the tuning of the relative values of these penalty parameters is not at all a technical subtety but a discernment of something important about hockey itself" (higher penalty ⇒ narrower talent spread) | Static penalties |
| hockeyviz-xg8-D44 | Centering penalties | Constraint Σ_s β_s·c_s = 0 (c_s = shot prevalence) enforced by adding 10⁶·c_s·c_t to penalty matrix entries; author coined the term "centering penalties" | larger multiples "can cause oscillations in the (necessarily iterative) fitting algorithm" | appendix: Centering Penalties |
| hockeyviz-xg8-D45 | Fusion (smoothing) penalties | Adjacent hexes p,q fused with strength c_pq = 0.2 · min(m,n)/√(mn) (m,n = shot counts in each hex): penalty on (β_p−β_q)² via ±c_pq entries in K | physical smoothness prior, but shot-count-aware: different shot volumes in adjacent hexes signal "something happens" there, so fuse less; fusing "effectively lowers the number of covariates" | Fabric Penalties |
| hockeyviz-xg8-D46 | Net-front exception | Fusion penalties for adjacencies involving the net-front hexagon weakened by a factor of 100 | net-front is "qualitatively very different from all the other parts of the rink (the league helpfully paints this area so that you will not forget)" | Fabric Penalties |
| hockeyviz-xg8-D47 | Dynamic penalties (season chaining) | Fit every season 2007-08→present; each person's previous estimate becomes their prior (β₀), penalized with strength 5·√(previous-season shots), floored at 200 shots (skaters) / 1000 (goalies) | player ability "varies slowly"; √n matches sampling intuition; "The factor of five is entirely ad hoc" | Dynamic Penalties |
| hockeyviz-xg8-D48 | Rookie priors | New skaters: −0.025 logits/shot prior from 200 imaginary shots (shooting AND setting, every layer); new goalies: +0.025 logits/shot from 1000 imaginary shots | a first-year NHLer is known a priori to be a "borderline" player (signed and rostered, but not previously); imaginary shots gradually replaced by real ones | Dynamic Penalties |
| hockeyviz-xg8-D49 | Hex dynamic penalty | Hex terms also anchored season-to-season: strength 0.5·√(shots from that hex the previous year) | "the content of these terms is primarily physical in nature and thus should not vary sharply" | Dynamic Penalties |
| hockeyviz-xg8-D50 | Penalty tuning protocol | Full hyperparameter search declared infeasible "with civilian-level computational power"; instead each human-term penalty verified to beat at least one nearby larger AND one smaller value out-of-sample | local-optimum-only validation, stated openly | Static penalties |
| hockeyviz-xg8-D51 | Term-admission criteria | Terms need intrinsic explanatory plausibility and/or out-of-sample predictive power; both together = "a satisfying 'scientific' model"; rejected ideas chronicled | frames the whole "Things That Did Not Help" section | Things That Did Not Help |
| hockeyviz-xg8-D52 | Rejected: score × rush/cycle interactions | Interaction terms for each score-state × rush/cycle combination improved prediction "very slightly" but not enough to justify the raft of extra terms — EXCLUDED | motivation was leading-team passive-defence/counterattack story | Things That Did Not Help |
| hockeyviz-xg8-D53 | Rejected: location-specific person skill | Splitting shooter/goalie terms into "interior" vs "perimeter" versions: predictive improvements "vanishingly small" — EXCLUDED | too many terms for the gain | Things That Did Not Help |
| hockeyviz-xg8-D54 | Rejected: diffuse on-ice shot-quality impact | General per-player terms applied to every shot while on ice (offence and defence, beyond shooting/setting) made predictions WORSE; "no evidence that defending players have a general impact on per-shot success" | defence is "primarily temporal" (suppressing rates/time) not per-shot-quality — consistent with visible rate impacts | Things That Did Not Help (carried from prior year) |
| hockeyviz-xg8-D55 | Simultaneous estimation philosophy | Structural terms and person terms "must be measured simultaneously, inside a framework where they can be held in tension with one another" | structure vs player-evaluation questions are inseparable | Tiny Philosophical Aside |
| hockeyviz-xg8-D56 | Findings: skill correlations | Cross-layer person-skill correlations nearly all feeble (\|r\| ≤ 0.09 for skaters; goalie miss↔stop −0.01) EXCEPT goalie freeze↔stop −0.28: freezing consistency trades off vs stopping unfrozen shots | "presumably it is being (partially?) driven by goaltending choices" | Correlations |
| hockeyviz-xg8-D57 | Findings: year-over-year stability | Year-over-year correlations of person terms: defenders +0.85…+0.93, forwards +0.81…+0.92, goalies +0.74…+0.87 across layers; author notes priors enforce some of this | table reproduced in §6 below | Correlations |
| hockeyviz-xg8-D58 | Trend observations | Constant terms drifting: more misses and more blocks league-wide recently (cites Prashanth Iyer); rush/cycle premium over open play has REVERSED in recent seasons; author flags these as not fully understood, possibly partly measurement-system changes | "These terms are very interesting to me because they have changed in impact in the last few years, in a way that does not feel settled" | Results; Previous Events |
| hockeyviz-xg8-D59 | Roadmap | Nothing queued for next year: 3-4 months of work this cycle exhausted the promising ideas | "there aren't any ideas worth mentioning for the moment" | Things That I Intend To Do Next Year |

## 4. Model structure sketch

Sequential conditional cascade (each layer conditions on surviving all previous layers):

```
shot taken (any attempt; empty-net & penalty-shot/shootout shots excluded)
  └─ Layer 1: at net vs BLOCKED            p_at   (blocked-origin location imputed)
      └─ Layer 2: on net vs MISSED          p_on
          └─ Layer 3: in play vs FROZEN     p_in   (goalie-deflected-out-of-play = frozen)
              └─ Layer 4: GOAL vs rebound   p_go
xG = p_at · p_on · p_in · p_go
```

Each layer is an independent penalized logistic regression sharing the covariate families below, with these per-layer differences:

- **Goalies:** absent from Layer 1; present in Layers 2, 3, 4.
- **Setters:** present ONLY in Layers 3 and 4 (dropped from 1 and 2 for lack of OOS gain).
- **Shooters:** present per-layer, but NOT used for tip/deflection shots (improves prediction).
- **Location fabrics:** 16 in total = 4 shot types × 4 layers, each independently centred; hexes are fused to neighbours within a fabric.
- **Coaches:** two terms (for/against) per layer.

The blocked-shot origin and the setter identity are both imputed as probability distributions (fractional design-matrix rows), not point guesses. All categorical families are centred (shot-weighted zero mean) via penalty. Fitting is season-by-season with the previous season's β as a dynamic prior (chained since 2007-08).

## 5. Full feature/covariate list (as stated)

Per layer (logit-additive):

1. **Constant** (per-layer base rate).
2. **Strength state:** EV (5v5+4v4), 3v3, EA (extra attacker), PP, SH, PPv3 (5v3, 4v3). Centred.
3. **Region:** below goal line; beyond the nearest blue line; in-zone (the remainder). Centred family (together with shot-type terms).
4. **Shot type (in-zone):** wrist/snap (incl. cradle/"michigan", bat, poke, wraparound), slap, tip/deflection, backhand. Centred.
5. **Location:** per-shot-type hex fabrics (88 cm-side hexagons, symmetrized L/R); tip fabric restricted to dot-to-dot/top-of-slot; backhand fabric small with an explicit "perimeter" term; blocked shots enter via imputed origin distribution; out-of-fabric tips get moved-toward-far-post imputed locations. 16 centred fabrics.
6. **Previous-event context (5 s window):** open play / cycle / rush. Centred.
7. **Cycle sub-type:** previous shot, turnover, hit thrown, hit taken, faceoff won, faceoff lost. Centred.
8. **Rebound delay:** 1, 2, 3, 4, or 5 seconds since the previous shot. Centred.
9. **Rebound shooter:** same shooter vs teammate. Centred.
10. **Rush sub-type:** previous shot, turnover, hit thrown, hit taken, faceoff. Centred.
11. **Time-in-period:** first minute / middle / final minute. Centred.
12. **Score state:** leading/tied/trailing × period 1/2/3 + garbage time (≥5 in P1, ≥4 in P2, ≥3 in P3). Centred.
13. **Sequence index:** 1st, 2nd, 3rd, 4th-or-later shot of a "sequence" (shot chain persisting while ≥1 defending skater stays on ice). Centred.
14. **Shooter identity** (except tips). Centred league-wide.
15. **Setter identity** (Layers 3-4 only; imputed fractional encoding; ×0.8 unassisted discount). Centred.
16. **Goalie identity** (Layers 2-4). Centred.
17. **Coach for / coach against** (per head coach). Each centred.

Explicitly NOT included: team identities; shooter terms on tips; setter terms in Layers 1-2; general per-player on-ice shot-danger terms; score×rush/cycle interactions; location-split (interior/perimeter) person terms; per-minute time terms; time-in-shift fatigue terms. NOT mentioned at all in the article (notable absences, (inferred) from silence): home/away, shooter handedness, continuous distance/angle covariates (location is entirely hex-categorical), pre-shot puck x/y delta or lateral-movement ("royal road") features, shift start (faceoff vs on-the-fly), travel/rest.

## 6. Evaluation protocol and reported results

**Protocol (as stated):**
- Out-of-sample predictive comparison is the working gate for including/excluding terms ("extrinsic predictive power"), paired with an intrinsic-plausibility criterion. Specific applications reported: per-minute time terms rejected (no accuracy gain); setter terms dropped from Layers 1-2 (gain too small); shooter identity dropped for tips (dropping IMPROVES prediction); interaction/diffuse-impact ideas rejected (§Things That Did Not Help); goalie miss-forcing kept partly because "it both increases prediction accuracy and is also mildly repeatable".
- Penalty hyperparameters: each human-term penalty verified to produce better out-of-sample predictions than at least one nearby larger and one smaller value; full search infeasible.
- No overall headline accuracy metric (log loss, AUC, calibration) for v8 vs v7 appears in the rendered article. (The page's HTML contains a commented-out, NON-rendered remnant from the xG6 write-up comparing v5 vs v6 out-of-sample log loss; it is not part of xG8 and is not reported here as such.)

**Reported quantitative results (rendered article):**
- Base rates: ~20% of shots blocked; ~2/3 of unblocked on net; ~25% of on-net frozen; ~8-9% of unfrozen on-net scored.
- Shot-context mix: ~70% open play, just under 25% cycle, ~5% rush.
- Hex location terms span roughly −2.5 to +2.5 logits (largest family).
- Cross-skill Pearson correlations: defenders block↔stop +0.04, miss↔stop −0.01, stop↔in-play +0.01; forwards +0.06, −0.05, +0.09; goalies miss↔stop −0.01, stop↔in-play −0.28.
- Year-over-year correlations: Defenders — block +0.93, miss +0.86, frozen +0.85, in-play/scored +0.92. Forwards — +0.91, +0.86, +0.81, +0.92. Goalies — miss +0.74, frozen +0.87, in-play/scored +0.78.
- Anecdotal extremes: 2008-09 had exactly 100 rush-after-faceoff shots with zero goals; a sequence of length 14 was observed in testing.

## 7. Outputs / artifacts

- Per-shot xG (product of the four layer probabilities).
- Per-layer person impact estimates in logits: shooter (block/miss/goal, plus see Open Questions), setter (freeze/goal), goalie (miss/freeze/goal), coach for/against (all four layers) — presented as league scatter/summary plots per layer, labeled by 2024-25 team(s).
- Historical term plots for every structural term, per season 2007-08→2024-25 (constants, strength states, regions, shot types, previous-event/cycle/rush sub-terms, rebound delay/shooter, time, score, sequence).
- Per-player career "sub-skill breakdown" history pages (every player since 2007-08) — available to site subscribers; illustrated with goalie style comparisons (Lundqvist deep-crease/low-freeze/high-stop; Luongo high-freeze; Quick aggressive/miss-forcing) and shooter examples (Draisaitl, Weber, Gallagher).
- League-wide distribution plots of person impacts per layer, both per-shot and weighted by season shot volume — used to argue right-skew of salient (selected-on) skills and to compare actor classes (e.g., setters' per-shot influence "as strong as that of shooters"; goalies largest at season level on the goal layer).
- Byproduct estimates named up front: shooting talent, shot-stopping talent, "certain aspects of coaching abilities".

## 8. Linked / companion articles

Visible (rendered) references:
- Prashanth Iyer, "It's harder than ever to get a shot (on net)" — https://prashanthiyer.substack.com/p/its-harder-than-ever-to-get-a-shot (cited for rising miss/block rates).
- Wessel van Wieringen, "Lecture notes on ridge regression" — https://arxiv.org/pdf/1509.09169.pdf (fitting methodology, §5/§5.2 followed).
- Corey Sznajder (@ShutDownLine) hand-tracked data — https://twitter.com/ShutDownLine (source of setter-imputation proportions and the ~20% unassisted figure).

Present in HTML but commented out (NOT rendered; listed for completeness only):
- https://hockeyviz.com/txt/xg5 (the 2021 model write-up the exposition descends from).
- https://hockeyviz.com/txt/xg6/0708 … /txt/xg6/2122 (per-season historical results pages for xG6).

No companion pages were fetched (the article is methodologically self-contained; its three appendixes are in-page). /howto/isolate and /howto/shotMap are covered by sibling agents per task instructions.

## 9. Open questions / ambiguities in the source

1. **Shooter terms: three or four layers?** The Shooters section says "a triple of terms ... (one for each submodel)" — but there are four submodels in v8, and the year-over-year correlation table lists four skater layers (block/miss/frozen/in-play-scored). "Triple" appears to be a leftover from an earlier 3-layer version (inferred); most likely shooters have terms in all four layers.
2. **"All three of the submodels"** — the Fitting section opens "All three of the submodels here are fit with so-called generalized ridge penalties" despite four submodels; another apparent version-update artifact (inferred). Assumed to apply to all four.
3. **Neutral-zone region granularity** — the prose describes below-goal-line and "beyond the blue line" shots, but exact handling of neutral-zone shots between the blue lines vs beyond the far blue line is only partly spelled out (figure-dependent; figures not retrieved).
4. **Rush/cycle zone determination for the 5 s window** relies on the recorded zone of the preceding PBP event; the article does not describe how event zones are themselves derived or corrected.
5. **Setter imputation for non-standard deployments** (e.g., 6 attackers, 3F/2D assumptions at special teams) is not addressed; the worked examples assume 3F/2D on ice.
6. **PPv3 vs PP boundary** — PP is "usually against four skaters"; whether 6v4 (extra attacker on the PP) falls under PP, EA, or PPv3 is not stated.
7. **No v8-vs-v7 accuracy comparison** is given in the rendered article, so the aggregate predictive value of the freeze-layer split and rush/cycle rework is asserted structurally rather than demonstrated numerically.
8. **Dynamic-prior interaction with centring** — how the season-chained priors and the per-season centring constraint interact (players entering/leaving shifting the centred zero) is not discussed.
9. **The garbage-time term's overlap with score×period terms** (whether garbage-time shots also carry their leading/trailing×period term) is not specified.
10. **"Perimeter" handling for non-backhand fabrics** — a perimeter concept is explicit for backhands (and used in a rejected interior/perimeter experiment), but whether wrist/slap fabrics have their own perimeter/out-of-fabric pooling is not stated in prose (figure-dependent).

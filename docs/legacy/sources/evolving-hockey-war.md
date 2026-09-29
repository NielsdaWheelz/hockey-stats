# Evolving-Hockey — WAR / GAR / RAPM Model ("Wins Above Replacement", 3-part series)

- **Title (primary):** "Wins Above Replacement" — Part 1: "History, Philosophy, and Objectives"; Part 2: "The Process"; Part 3: "Replacement Level, Decisions, Results, and Final Remarks"
- **Authors:** Josh Younggren & Luke Younggren (EvolvingWild / Evolving-Hockey; the Hockey-Graphs author account appears as "lukesolberg")
- **URLs actually used (all fetched):**
  - Part 1: https://evolving-hockey.com/blog/wins-above-replacement-history-philosophy-and-objectives-part-1/ (site republication dated April 26, 2021; originally Hockey-Graphs, January 2019 — the republication states January 6, 2019)
  - Part 2: https://evolving-hockey.com/blog/wins-above-replacement-the-process-part-2/ (republication April 26, 2021; original January 2019)
  - Part 3: https://evolving-hockey.com/blog/wins-above-replacement-replacement-level-decisions-results-and-final-remarks-part-3/ (republication April 27, 2021; original January 2019)
  - Companion 1 (load-bearing RAPM spec Part 2 defers to): https://hockey-graphs.com/2019/01/14/reviving-regularized-adjusted-plus-minus-for-hockey/ (published Jan 14, 2019; updated Jan 18, 2019)
  - Companion 2 (load-bearing penalty-component spec Part 3 defers to): https://hockey-graphs.com/2019/01/15/penalty-goals-an-expanded-approach-to-measuring-penalties-in-the-nhl/ (published Jan 15, 2019; updated Jan 18, 2019)
  - Site overview (fetched; confirmed to be a marketing stub, no methodology): https://evolving-hockey.com/evolving-hockey-overview/
- **Accessed:** 2026-07-03
- **Retrieval note:** all five methodology pages were retrieved via WebFetch extractions. Everything below is sourced from those retrievals; inferences are marked "(inferred)". Some numeric tables in the articles are embedded images (per-component replacement rates, ensemble weights, final SPM feature lists, goals-per-win by season) and their exact values were NOT transcribable — noted where relevant. The evolving-hockey.com overview page confirms a parallel **xGAR** model and goalie GAR tables exist on the site but documents neither; no newer public methodology document superseding the 2019 series was found.

## 2. Summary

Evolving-Hockey's WAR is a deliberately **descriptive** (not predictive) single-number value framework: it converts everything a skater measurably did into Goals Above Replacement (GAR) and then into wins (WAR) / standings points (SPAR), explicitly modeled on baseball's WAR philosophy and explicitly rejecting the true-talent/expected-value orientation of prior hockey WAR models (WOI, Sprigings, Perry). The engine is a two-stage design: first, **long-term RAPM** — weighted ridge regressions on shift-level rows (each shift duplicated into offensive and defensive observations) with separate per-player offense/defense dummies plus score-state, zone-start, back-to-back, home, and strength covariates — produces stable 11-year (2007-08–2017-18) per-60 player coefficients; second, single-season **SPM (Statistical Plus-Minus)** models regress those long-term RAPM coefficients on single-season box-score/RTSS aggregates via a weighted ensemble (3 algorithms × 8 components = 24 sub-models), because single-season RAPM is still too collinear. Components are EV offense, EV defense, PP offense, and SH defense (each fit separately for forwards and defensemen), plus a penalties component (drawn + taken) valued by fixed league-average "penalty goals" (0.182 goals per standard minor); there is no faceoff component (faceoff % is only a covariate) and no SH-offense/PP-defense component. Offense targets use actual **goals** (GF RAPM) to stay descriptive; defense targets use **xGA** because skaters can't control finishing against them and goalies (who never leave the ice) can't be separated from skaters in a goals-based regression — goalies are excluded from skater WAR entirely and live in a separate, here-undocumented model. Replacement level is a "poor man's" TOI-depth-chart pooling (below top-13F/7D at EV, top-11 PP, top-9 SH per team), computed **independently per component/strength state**, which the authors acknowledge makes league-total WAR fluctuate year-to-year — "likely the most controversial aspect." Goals convert to wins via a Pythagorean expectation with a fitted NHL exponent of 2.091, season-specific goals-per-win. No formal validation is presented in the series (deferred to a future article); the code is public on GitHub, an informal ±0.5-win error range is suggested, and the SH-defense component is self-flagged as "the shakiest part of our model."

## 3. Decision inventory

| id | topic | decision | rationale / verbatim quote | article section |
|---|---|---|---|---|
| evolving-hockey-war-D1 | philosophy: descriptive stance | WAR measures value-to-date (what happened), not true talent or future performance; explicitly reverses the predictive orientation of prior hockey WAR models | "We want a model that measures what a player did; how a player added value directly tied to wins."; baseball WAR is "descriptive in nature" | Part 1 |
| evolving-hockey-war-D2 | currency | Goals are the base unit (GAR), converted to wins afterward — mirroring baseball's runs→wins chain | goals have a "direct tie to Wins, as in baseball" | Part 1 |
| evolving-hockey-war-D3 | design goals | Six goals: all measurable contributions adjusted for context/teammates/competition; goals basis; daily in-season updates; rookies evaluated identically to veterans (no experience prior); interpretability (no black box); alignment with end-of-year awards | stated as the model's objectives list | Part 1 |
| evolving-hockey-war-D4 | framework pluralism | WAR is a framework with no single correct version; predictive and descriptive variants can coexist | "The great thing about WAR is that it is a framework—there is no single correct version."; "There is no obvious right answer here" | Part 1 |
| evolving-hockey-war-D5 | luck | Luck is deliberately INCLUDED in the results (consequence of descriptive goals basis); amount acknowledged as unquantifiable | "Hockey is a very random sport—luck plays a major factor"; "the amount of luck included here will likely be hard to determine" | Part 1, Part 3 |
| evolving-hockey-war-D6 | prior work | Surveyed lineage: Ryder Player Contribution (2003), ThoR (2012-13), War-On-Ice (2014), Sprigings (2016), Perry/Corsica (2017), Arsenoff (2018); declined to characterize Sprigings' model absent public documentation | "It would be both unwise and a disservice if we attempted to summarize Sprigings' model without a public write-up" | Part 1 |
| evolving-hockey-war-D7 | data & era | NHL RTSS play-by-play, RTSS era only; long-term models span 11 seasons, 2007-08 through 2017-18 | RTSS availability defines the era | Part 2, RAPM companion |
| evolving-hockey-war-D8 | RAPM unit of observation | Row = shift (continuous segment with no substitutions), duplicated into two rows per shift (home-attacking / away-attacking) so offense and defense are separate observations; EV design matrix 586,018 rows × 1,794 columns (2017-18 demo) | duplication yields separate offensive/defensive impact per player | RAPM companion |
| evolving-hockey-war-D9 | RAPM response | Response = within-shift rate per 60: CF60 primary demo; GF60 and xGF60 variants fit as parallel models | mean EV CF60 = 62.12, "not directly comparable to standard CF60" | RAPM companion |
| evolving-hockey-war-D10 | RAPM player encoding | Every skater gets TWO binary predictors — one offensive, one defensive (1 when on ice for that side's row) — following Ilardi–Barzilai | presence of player on offense/defense yields separate coefficients | RAPM companion |
| evolving-hockey-war-D11 | RAPM non-player covariates | Score state (7-level categorical, home/away-specific), strength state (5v5/4v4/3v3 within the EV model), zone start (O-zone vs D-zone faceoff, home/away-specific), back-to-back (home/away-specific), home-team indicator | context that confounds on-ice rates must be in the design matrix | RAPM companion |
| evolving-hockey-war-D12 | RAPM weighting | Weighted least squares with shift length in seconds as the weight | "longer shift has more 'weight' in final model"; mean shift 12.94 s | RAPM companion |
| evolving-hockey-war-D13 | regularization class | Ridge (L2/Tikhonov), NOT LASSO: LASSO could zero out one member of a heavily-paired duo, unacceptable for individual ratings; ridge = Gaussian mean-0 prior, quasi-Bayesian shrinkage of low-TOI players to league mean | "when a pair of players play together for a significant amount of time...coefficient estimates...will be extremely unstable" (Sedins >90% together) | RAPM companion |
| evolving-hockey-war-D14 | lambda selection | λ via 10-fold cross-validation: `cv.glmnet(x, y, weights = length_shift, alpha = 0, nfolds = 10, standardize = FALSE, parallel = TRUE)` | standard glmnet CV; chosen λ values not reported | RAPM companion |
| evolving-hockey-war-D15 | strength-state partition (RAPM) | EV model pools 5v5+4v4+3v3; a separate special-teams model uses four shift versions (home/away × up/down a skater), yielding four coefficients per player: PP offense, PP defense, SH offense, SH defense | play differs by strength; special teams need their own design | RAPM companion |
| evolving-hockey-war-D16 | goalies in RAPM | Goalies excluded from the Corsi RAPM; included as defense-ONLY variables in the GF60 RAPM (zero offensive impact assumed) | goalies affect goals against, not shot attempts for | RAPM companion |
| evolving-hockey-war-D17 | inclusion threshold & shrinkage | All skaters with >1 EV minute enter the regression; players under ~100–150 EV min are effectively regressed to 0 — accepted as the ridge design working as intended | "In OLS regression, these [low-minute] players would have wildly inflated per 60 ratings" | RAPM companion |
| evolving-hockey-war-D18 | inference honesty | No standard errors/t/p-values published — regularized coefficients are biased and "not considered true unbiased estimators"; magnitudes "likely somewhat smaller than what the actual values should be" | flagged as an interpretation caveat, not fixed | RAPM companion |
| evolving-hockey-war-D19 | two-stage architecture | Long-term (11-yr) RAPM coefficients become TARGETS for single-season SPM models built from RTSS box-score aggregates; long-term player inclusion uses a TOI cutoff chosen by cross-validation (details deferred to RITSAC '18 slides) | "Within a single season, multicollinearity can still be an issue with the RAPM method." | Part 2 |
| evolving-hockey-war-D20 | component decomposition | Components: EV offense, EV defense, PP offense, SH defense — each fit separately by position (F/D) → 8 SPM component models; penalties added as a 9th post-model component; NO SH-offense/PP-defense components; NO faceoff component (FO% is only a covariate) | component structure follows where value is measurable and separable | Part 2, Part 3 |
| evolving-hockey-war-D21 | goals vs xG asymmetry | Offense targets = GF RAPM (actual goals); defense targets = xGA RAPM. Offense stays descriptive ("some players do certain things on offense that xG models do not capture well"); defense uses xGA because skaters can't control finishing against them | "skaters have no control (or very little control) over whether a shot results in a goal being scored against them" | Part 3 |
| evolving-hockey-war-D22 | Corsi rejected as value basis | Shot attempts rejected as the WAR value metric (kept only inside RAPM/features) | "we feel shot attempts do not mirror actual goal scoring as closely as we'd like" | Part 3 |
| evolving-hockey-war-D23 | SPM algorithm pool | Candidates: OLS, elastic net, linear-kernel SVM, Cubist, bagged MARS; final ensemble = 3 algorithms per component → 24 sub-models; gradient boosting tested and beaten by linear methods | "linear regression works very well for this problem... extremely difficult to beat when tuned properly." | Part 2 |
| evolving-hockey-war-D24 | ensemble weighting | Weights per component chosen by grid search minimizing out-of-sample RMSE over 300 cross-validated 80/20 train/test splits | aggregated RMSE across runs is the selection criterion | Part 2 |
| evolving-hockey-war-D25 | feature selection | Pre-removal of Points, state-adjusted metrics, adjusted G/A1/A2; collinear rel-TM family (CF/FF/SF/xGF) reduced to one representative per training run; 300 CV runs per tuning iteration | multicollinearity management inside SPM | Part 2 |
| evolving-hockey-war-D26 | rel-TM redefinition | Relative-to-teammate metrics recomputed using the TOTAL number for a player's teammates (not the standard public-site version) | "metric actually correlates better with the RAPM outputs if...we use the total number for a given player's teammates" | Part 2 |
| evolving-hockey-war-D27 | team adjustment | Adapted from Daniel Myers' BPM team adjustment: `(factor × TeamStat − Σ(player %min × raw SPM)) / TeamSkaters`; factors tuned over 0.1–3.0 (step 0.05) by correlation of summed SPM vs 11-yr RAPM: EVO 1.6, EVD 1.4, PPO 1.3, SHD 1.3 | "In a single season, it is something that we need to apply an adjustment for."; change "somewhat minimal" | Part 2 |
| evolving-hockey-war-D28 | distributional justification | Long-term RAPM outputs are "quite normally distributed" → linear model classes favored for SPM | shown via histogram of forward EV GF RAPM | Part 2 |
| evolving-hockey-war-D29 | variable importance withheld | Deliberately do NOT publish variable-importance numbers | they are "misleading, hard to interpret...and not all that helpful"; SVM importance "shaky at best" | Part 2 |
| evolving-hockey-war-D30 | replacement level definition | "Poor man's replacement": pool all players below per-team TOI depth cutoffs — EV: top 13 F + 7 D; PP: top 11; SH: top 9 — the below-threshold pool's aggregate rate IS the replacement player; league-minimum-salary definition tested and rejected (too few qualifying players) | Bill James: "Drop under it and they release you." | Part 3 |
| evolving-hockey-war-D31 | per-component replacement | Independent replacement baselines per component: EV (per position), PP offense, SH defense, penalties — contra baseball's single replacement player, because deployment differs by strength state | Tango: "there are only replacement level PLAYERS..." but "Alex Ovechkin...completely different players when looking at EV performance vs. PP performance" | Part 3 |
| evolving-hockey-war-D32 | GAR arithmetic | GAR = GAA (above-average) + TOI × replacement rate; e.g. PPO forwards: −251.7 pooled goals / 39,063.9 min × 60 = −0.3866/60 replacement rate; Taylor Hall '17-18: 6.4 PPO GAA → 7.8 PPO GAR | worked examples given | Part 3 |
| evolving-hockey-war-D33 | goals→wins conversion | Pythagorean expectation with fitted NHL exponent 2.091 (minimize squared deviation of pythagorean win% vs actual, shootout goals excluded); season-specific Goals-per-Win divides each player's GAR (formula reported as GpW = 4 × league GF/game ÷ exponent — see Open Questions) | "traditional baseball method"; per-season GpW chart provided (image) | Part 3 |
| evolving-hockey-war-D34 | floating league total | Accepted consequence: league-total WAR varies year-to-year (baseball's is fixed) because component replacement levels are independent | "likely the most controversial aspect of our model from a historical point of view" | Part 3 |
| evolving-hockey-war-D35 | SH defense caveat | Replacement-level SH defense ≈ league average (near-zero GAR available) because replacement-tier players actually get PK minutes; component self-flagged as weakest | "the shakiest part of our model"; "recommend the SHD component be taken with a grain of salt, especially in-season" | Part 3 |
| evolving-hockey-war-D36 | goalie treatment | Goalies fully excluded from skater WAR; goals-based skater-defense RAPM rejected because goalie/skater separation is impossible ("goalies never leave the ice" → fatal multicollinearity); goalie value handled in a separate model NOT documented in this series (site has Goalie GAR tables) | "No acceptable method has been developed...to properly separate skaters from the goalies that play behind them" | Part 3 |
| evolving-hockey-war-D37 | penalties component | Penalties taken + drawn = one component, valued in fixed "penalty goals" and added post-SPM; magnitudes ASSUMED commensurate with SPM components (flagged: RAPM shrinkage may make this "not exactly correct"); per-strength-state penalty evaluation blocked by RTSS recording limits | penalty article supplies the goal values | Part 3, Penalty companion |
| evolving-hockey-war-D38 | penalty inclusion rules | Count only strength-state-changing minors/double minors/majors/penalty shots; EXCLUDE offsetting penalties (net zero), fights/misconducts (no state change), too-many-men/bench minors, delayed-penalty cases (unrecorded by NHL), and unattributable penalty clusters | "Offsetting penalties are excluded as the net goal impact is equal to zero." | Penalty companion |
| evolving-hockey-war-D39 | penalty goal value | Value per penalty from league-average rate differentials: ((5v4GF60−5v5GF60)+(5v4GA60−5v5GA60)) × 120/3600 = **0.182 goals** per standard 5v5→5v4 minor (11-season league averages: 5v5 GF60 2.271, 5v4 GF60 6.250, 5v4 GA60 0.790) | "A player does not have control over whether that player's team scores a goal in the ensuing powerplay" → league-average value, not realized outcome | Penalty companion |
| evolving-hockey-war-D40 | non-5v5 penalties | Penalties taken while already special-teams are compounded over remaining time at each resulting state (e.g. penalty 30 s into a 5v4 → 90 s of 5v4→5v3 + 30 s of 5v5→5v4 = 0.419 goals); ~25% of penalties are non-5v5 | "25% of all penalties taken impact team goal rates in a different way" | Penalty companion |
| evolving-hockey-war-D41 | major/penalty-shot asymmetry | Major: taker −0.455 (5 min) but drawer only +0.182 — "the player drawing the penalty did not do anything additional to earn the extra 3 minutes"; penalty shot: drawer +0.3194 (league shootout conversion), taker −0.182 (subjective, flagged) | asymmetric credit by design | Penalty companion |
| evolving-hockey-war-D42 | penalty position centering | Penalty Goals Above Average = player rate minus POSITION-average rate × TOI (forwards draw more, defensemen take slightly more) | centers each position at zero for cross-position comparison | Penalty companion |
| evolving-hockey-war-D43 | penalty score/venue adjustment | Multiplicative score/venue factors on penalty frequency: home trailing 1.175, tied 1.056, leading 0.919 (applied equally to taken and drawn, all strength states); PP/SH-specific adjustment attempted and abandoned ("too difficult to parse at this time") | trailing teams take more penalties, leading teams fewer | Penalty companion |
| evolving-hockey-war-D44 | uncertainty communication | Informal ±0.5-win error range proposed (half baseball's ±1) while admitting the methods produce no real error estimates | "methods...did not allow us to determine error estimates" | Part 3 |
| evolving-hockey-war-D45 | validation & reproducibility | No formal validation in the series — deferred to a future article; full R code public (github.com/evolvingwild/evolving-hockey); outputs published on the site; WAR framed as "a starting point" for analysis, not an endpoint; independent testing invited | "If you'd like to test out how well our WAR model does, please feel free to test it." | Part 3 |
| evolving-hockey-war-D46 | xGAR sibling (post-series) | The site later added a parallel **xGAR** model ("deserved"/expected orientation) with mirrored components/pages; NOT documented in the 2019 series or on the overview page | "All of the features that utilize GAR have parallel xGAR pages/tools as well." | Site overview |
| evolving-hockey-war-D47 | display/reporting conventions | Distribution charts use 60+ min TOI cutoffs and exclude the 2012-13 lockout season; results presented with a rule-of-thumb tier table (e.g. 6+ WAR ≈ MVP-caliber, 2–3 ≈ All-Star), replicating Justin Bopp's Beyond the Boxscore bins | interpretive scaffolding for the single number | Part 3 |

## 4. Model structure sketch

```
NHL RTSS play-by-play (2007-08 … 2017-18)
        │
        ├──► Long-term RAPM (11-yr, per component, per position)          [Stage 1]
        │      weighted ridge on duplicated shift rows
        │      • EV model (5v5/4v4/3v3 pooled): response CF60 / GF60 / xGF60
        │      • Special-teams model: 4 shift versions → PP off/def, SH off/def coefs
        │      • player off + def dummies; score state, zone start, B2B, home, strength
        │      • targets used downstream: GF RAPM (offense), xGA RAPM (defense)
        │
        ├──► Single-season SPM (Statistical Plus-Minus)                    [Stage 2]
        │      8 models = {EVO, EVD, PPO, SHD} × {F, D}
        │      predictors: single-season box/RTSS aggregates (see §5)
        │      targets: the long-term RAPM coefficients
        │      ensemble: 3 algorithms/component (24 sub-models),
        │                weights by grid search over 300 CV 80/20 splits (min RMSE)
        │
        ├──► Team adjustment (Myers BPM-style)                             [Stage 3]
        │      factor × team stat − Σ(%min × raw SPM), factors 1.6/1.4/1.3/1.3
        │
        ├──► Penalty component (separate path, no regression)
        │      penalty goals: fixed league-average values (0.182/minor etc.)
        │      × score/venue factors → position-centered above-average
        │
        ├──► Replacement offset (per component, per position)              [Stage 4]
        │      GAR = GAA + TOI × pooled below-depth-chart replacement rate
        │
        └──► Wins conversion                                               [Stage 5]
               WAR = GAR / season Goals-per-Win (pythagorean, exponent 2.091)

Goalies: excluded from all of the above; separate (undocumented-here) goalie model.
xGAR: later parallel pipeline with expected-goals orientation (undocumented here).
```

What conditions on what: SPM conditions on RAPM (as target); the team adjustment conditions on both raw SPM and long-term RAPM (factor tuning); replacement and wins conversion are affine transforms applied after modeling; the penalty component bypasses the regression machinery entirely and is only reconciled by the magnitude-commensurability assumption (D37).

## 5. Full feature/covariate list as stated

### RAPM design matrix (companion article; EV model)
- Per-skater offensive dummy + per-skater defensive dummy (every skater >1 EV min)
- Score state: 7-level categorical (down 3 … up 3), home/away-specific, one reference level dropped
- Strength state: 5v5 / 4v4 / 3v3 (within EV model)
- Zone start: offensive- vs defensive-zone faceoff, home/away-specific
- Back-to-back: binary, home/away-specific
- Home-team indicator: binary
- Shift length (seconds): regression weight, not a predictor
- Goalies: defense-only dummies in the GF60 model; absent from CF60 model

### SPM candidate predictor pool (Part 2, before feature selection)
Offensive metrics (EV and PP models): TOI%, TOI/GP; G, A1, A2, Points (+ `_adj` state-adjusted versions — removed pre-selection); iSF, iFF, iCF, ixG, iCF_adj, ixG_adj; giveaways GIVE (o/n/d zone splits, total, adjusted); takeaways TAKE (o/n/d, total, adjusted); hits for iHF (o/n/d, total, adjusted); hits against iHA (o/n/d, total, adjusted); zone-start percentages OZS/NZS/DZS; FO_perc and regressed r_FO_perc; rel-TM family rel_TM_{GF60, xGF60, SF60, FF60, CF60} plus `_state` versions.

Defensive metrics (EV and SH models): TOI_perc, TOI_GP; iBLK, iBLK_adj; GIVE/TAKE/iHF/iHA families as above; OZS/NZS/DZS; FO_perc, r_FO_perc; rel_TM_{SA60, FA60, CA60, xGA60} plus `_state` versions.

Removed before final selection: Points, state-adjusted metrics, adjusted G/A1/A2; the collinear rel-TM shot-family reduced to one representative per training run. **Final per-component feature lists are shown only in embedded images and were not transcribable.**

## 6. Evaluation protocol and reported results

- **No formal validation of WAR is presented in the series.** The authors explicitly defer: "studies evaluating the overall performance of the metric...will be saving that for its own article" (future link never present in the retrieved text).
- **SPM model selection metric:** out-of-sample RMSE aggregated over 300 cross-validated 80/20 splits, per component; a table of final-ensemble RMSE and R² per component exists but only as an image (values not transcribed).
- **Team-adjustment tuning:** correlation between summed single-season SPM and 11-year RAPM coefficients across multiplier grid 0.1–3.0.
- **GF vs xGF divergence evidence:** scatterplots of 11-year career GF-RAPM vs xGF-RAPM (forwards, defensemen) and 3-year examples; tables of outlier players at a 5000+ EV-minute threshold — used to justify keeping goals (not xG) on offense.
- **Team RAPM sanity check (companion):** team-aggregated RAPM vs raw per-60 R² ≈ 0.8–0.9; residual attributed to schedule/score/venue/seasonal environment.
- **Distributional results:** forward/defenseman WAR distributions 2007-18 (60+ min TOI, lockout excluded); league GAR/WAR totals by season chart (totals fluctuate — see D34); WAR tier table (6+ MVP-caliber, 2–3 All-Star, etc.).
- **Uncertainty:** proposed ±0.5 wins heuristic; explicitly no computable error estimates (D44).
- **Reproducibility:** R code public at https://github.com/evolvingwild/evolving-hockey (2026-07-03: URL now 404s — repo removed or private; only `hockey-all` remains public, see `evolving-hockey-xg.md` §10); all outputs published at https://evolving-hockey.com/. (Requires scraping NHL RTSS data.)
- **Development effort disclosure:** ~2 years (Aug 2017–Jul 2018), three full iterations; authors state the SPM ensemble "may be a bit excessive" and linear regression alone would nearly suffice.

## 7. Outputs / artifacts

- **GAR / WAR / SPAR** per skater, decomposed into components (EVO, EVD, PPO, SHD, Penalties), published as sortable tables on evolving-hockey.com; daily in-season updates (a stated design goal, D3).
- **RAPM charts/tables** per player (single-season and multi-year; CF/xGF/GF bases) — a standalone product on the site as well as the WAR substrate.
- **Goalie GAR tables** (separate model, undocumented in these sources).
- **xGAR** parallel tables/tools (post-series; undocumented in these sources).
- Skater/team/league summary tables and charts; WAR distribution and tier visuals in the articles.
- No spatial/map outputs anywhere in this framework — everything is scalar per player per component (contrast with HockeyViz).

## 8. Linked / companion articles referenced

Fetched for this distillation (the 2 allowed companions):
- https://hockey-graphs.com/2019/01/14/reviving-regularized-adjusted-plus-minus-for-hockey/ (RAPM spec)
- https://hockey-graphs.com/2019/01/15/penalty-goals-an-expanded-approach-to-measuring-penalties-in-the-nhl/ (penalty goals)

Referenced by the series (not fetched):
- RITSAC 2018 presentation: video https://www.youtube.com/watch?v=7nHoCBCdSlE&t=33m00s ; slides https://hockeygraphsdotcom.files.wordpress.com/2018/08/gar_spm_ritsac_18.pdf (holds the long-term-RAPM TOI-cutoff CV details)
- Their xG model writeup: http://rpubs.com/evolvingwild/395136/ (covered by sibling distillation evolving-hockey-xg.md)
- Relative shot metrics: https://hockey-graphs.com/2018/02/21/revisiting-relative-shot-metrics-part-1/ and .../2018/02/22/...-part-2/
- wPAR: https://hockey-graphs.com/2017/08/02/introducing-weighted-points-above-replacement-part-2/
- Code: https://github.com/evolvingwild/evolving-hockey (2026-07-03: 404 — removed/private; see `evolving-hockey-xg.md` §10)
- Prior hockey WAR: Ryder http://www.hockeyanalytics.com/Research_files/Player_Contribution_System.pdf ; ThoR (Sloan paper); WOI http://blog.war-on-ice.com/index.html%3Fp=429.html and replacement article ...?p=354 ; Perry http://corsica.hockey/misc/war_notebook.html + http://www.corsica.hockey/blog/2017/05/20/the-art-of-war/ ; Arsenoff RITSAC slides
- APM/RAPM lineage: Rosenbaum http://www.82games.com/comm30.htm ; Ilardi–Barzilai http://www.82games.com/ilardi2.htm ; Sill (Sloan RAPM paper); Brian Macdonald hockey APM papers https://arxiv.org/pdf/1006.4310.pdf , https://arxiv.org/pdf/1201.0317.pdf ; Myers BPM https://www.basketball-reference.com/about/bpm.html ; Gelman Bayesian APM post; Jacobs squared2020 RAPM deep dive
- McCurdy Magnus: https://hockeyviz.com/txt/magnusEV (covered by sibling agents — skipped)
- Baseball WAR philosophy: FanGraphs WAR library, Baseball Prospectus replacement-level history + Reworking WARP series, Tango WAR posts, openWAR https://arxiv.org/pdf/1312.7158.pdf , Woolner MLV
- Pythagorean: http://angrystatistician.blogspot.com/2016/06/whats-value-of-win.html ; https://worldsworstsportsblog.com/2015/03/17/a-pythagorean-exponent-for-the-nhl/

## 9. Open questions / ambiguities in the source

1. **Chosen λ values are never reported** for any RAPM model, nor is sensitivity to the 10-fold choice.
2. **Final SPM ensemble weights and feature lists live in images** — RMSE/R² per component and per-algorithm feature rankings are shown but not stated in text; not recoverable here.
3. **The goals-per-win formula as retrieved** ("GpW = (4 × League GF per Game)/exponent", exponent-fitting expression `((1+(GA/GF)^e)^-1) − (W/(W+L))^2` minimized) is likely a lossy paraphrase of Christopher Long's pythagorean win-value derivation — the exact algebra should be treated as unverified; the exponent 2.091 and shootout exclusion are stated plainly.
4. **How the penalties replacement level is computed** is not spelled out (Part 3 lists penalties among the four replacement baselines; the penalty companion has no replacement discussion).
5. **The goalie model is entirely undocumented** in these sources — only its existence (site tables) and the reason goalies are excluded from skater WAR are stated.
6. **xGAR methodology is undocumented** — the overview page confirms it exists as a "deserved" parallel model but gives no spec; it postdates the series.
7. **Long-term RAPM inclusion cutoff** ("TOI cutoff determined via cross-validation") is deferred to the RITSAC '18 presentation; not in the written record retrieved.
8. **Tension not resolved in text:** Part 3 (as retrieved) says RTSS "doesn't record when penalties occurred (strength-state timing)", yet the penalty companion compounds values across strength states while flagging state-specific TOI as "difficult to determine" due to delayed-penalty gaps — the precise data limitation boundary is ambiguous.
9. **Empty-net goals are not excluded** — raised by a reader comment on Part 3; no author response retrieved.
10. **League-total WAR non-conservation** (equal games ≠ equal total wins across seasons) — raised by a reader; acknowledged as a philosophical trade-off but not resolved.
11. **Whether the production model on evolving-hockey.com (2026) still matches the 2019 spec** is unverifiable from public documentation — the overview page points back at this series and no newer methodology write-up was found.
12. **Part 2's SPM "back-to-back / home-away" handling** — these appear as RAPM covariates but the SPM predictor pool (box-score aggregates) does not list them; whether any schedule context enters Stage 2 is unstated.
13. **Attribution nuance:** the retrieved RAPM byline reads "EvolvingWild (Luke Solberg et al.)" while the series is credited to Josh & Luke Younggren; treated as the same pseudonymous team (inferred).
